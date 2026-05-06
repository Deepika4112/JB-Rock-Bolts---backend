from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from datetime import datetime
import shutil
import os
import uuid
from app.database import get_db
from app.models.models import PurchaseOrder, POLineItem
from app.schemas.purchase_order import PurchaseOrderCreate, PurchaseOrderUpdate, PurchaseOrderOut

router = APIRouter(prefix="/api/purchase-orders", tags=["Purchase Orders"])


@router.post("/upload")
async def upload_po_file(file: UploadFile = File(...)):
    UPLOAD_DIR = "uploads"
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
    
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"file_url": f"/uploads/{unique_filename}"}


def _to_out(po: PurchaseOrder) -> PurchaseOrderOut:
    return PurchaseOrderOut(
        id=po.id,
        client_name=po.client_name,
        po_number=po.po_number,
        item=po.item,
        uom=po.uom,
        project=po.project,
        project_id=po.project_id,
        location=po.location,
        total_quantity=po.total_quantity,
        delivered_quantity=po.delivered_quantity,
        pending_quantity=po.pending_quantity,
        unit_price=po.unit_price,
        gst=po.gst,
        gst_rate=po.gst_rate,
        freight=po.freight,
        payment_terms=po.payment_terms,
        validity_date=po.validity_date,
        delivery_status=po.delivery_status,
        subtotal=po.subtotal,
        gst_amount=po.gst_amount,
        grand_total=po.grand_total,
        created_at=po.created_at,
        created_by=po.created_by,
        last_opened_at=po.last_opened_at,
        last_opened_by=po.last_opened_by,
        last_updated_at=po.last_updated_at,
        last_updated_by=po.last_updated_by,
        file_url=po.file_url,
        line_items=[
            {"id": li.id, "item": li.item, "quantity": li.quantity, "uom": li.uom, "unit_price": li.unit_price}
            for li in (po.line_items or [])
        ],
    )


@router.get("", response_model=List[PurchaseOrderOut])
def list_purchase_orders(
    search: Optional[str] = None,
    client: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(PurchaseOrder)
    if search:
        q = q.filter(
            PurchaseOrder.po_number.ilike(f"%{search}%")
            | PurchaseOrder.client_name.ilike(f"%{search}%")
            | PurchaseOrder.item.ilike(f"%{search}%")
        )
    if client:
        q = q.filter(PurchaseOrder.client_name.ilike(f"%{client}%"))
    orders = q.order_by(PurchaseOrder.created_at.desc()).offset(skip).limit(limit).all()
    return [_to_out(o) for o in orders]


@router.post("", response_model=PurchaseOrderOut, status_code=status.HTTP_201_CREATED)
def create_purchase_order(payload: PurchaseOrderCreate, db: Session = Depends(get_db)):
    data = payload.model_dump(exclude={"line_items"})

    # If line_items provided, set legacy fields from first item for backward compat
    if payload.line_items:
        first = payload.line_items[0]
        data["item"] = first.item
        data["uom"] = first.uom
        data["unit_price"] = first.unit_price
        data["total_quantity"] = sum(li.quantity for li in payload.line_items)

    po = PurchaseOrder(**data)

    # Create line items
    for li_data in payload.line_items:
        po.line_items.append(POLineItem(**li_data.model_dump()))

    db.add(po)
    try:
        db.commit()
        db.refresh(po)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Purchase order with PO# '{payload.po_number}' already exists.",
        )
    return _to_out(po)


@router.get("/{po_id}", response_model=PurchaseOrderOut)
def get_purchase_order(po_id: int, opened_by: Optional[str] = None, db: Session = Depends(get_db)):
    po = db.get(PurchaseOrder, po_id)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found.")
    if opened_by:
        po.last_opened_at = datetime.utcnow()
        po.last_opened_by = opened_by
        db.commit()
        db.refresh(po)
    return _to_out(po)


@router.put("/{po_id}", response_model=PurchaseOrderOut)
def update_purchase_order(po_id: int, payload: PurchaseOrderUpdate, db: Session = Depends(get_db)):
    po = db.get(PurchaseOrder, po_id)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found.")

    update_data = payload.model_dump(exclude_none=True, exclude={"line_items"})
    for field, value in update_data.items():
        setattr(po, field, value)

    # If line_items are provided, replace them
    if payload.line_items is not None:
        # Clear existing
        po.line_items.clear()
        # Add new
        for li_data in payload.line_items:
            po.line_items.append(POLineItem(**li_data.model_dump()))
        # Update legacy fields from first item
        if payload.line_items:
            first = payload.line_items[0]
            po.item = first.item
            po.uom = first.uom
            po.unit_price = first.unit_price
            po.total_quantity = sum(li.quantity for li in payload.line_items)

    po.last_updated_at = datetime.utcnow()
    db.commit()
    db.refresh(po)
    return _to_out(po)


@router.delete("/{po_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_purchase_order(po_id: int, db: Session = Depends(get_db)):
    po = db.get(PurchaseOrder, po_id)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found.")
    db.delete(po)
    db.commit()

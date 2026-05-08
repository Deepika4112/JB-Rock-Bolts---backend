from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import shutil
import os
import uuid
from app.database import get_db
from app.models.models import Sale, SaleActivity, PurchaseOrder, SaleItem, POLineItem
from app.schemas.sale import SaleCreate, SaleUpdate, SaleOut, SaleActivityCreate, SaleActivityOut, SaleItemCreate
from app.utils.helpers import generate_invoice_number

router = APIRouter(prefix="/api/sales", tags=["Sales"])


@router.get("", response_model=List[SaleOut])
def list_sales(
    po_id: Optional[int] = None,
    client: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(Sale)
    if po_id:
        q = q.filter(Sale.po_id == po_id)
    if client:
        q = q.filter(Sale.client_name.ilike(f"%{client}%"))
    return q.order_by(Sale.created_at.desc()).offset(skip).limit(limit).all()


@router.post("/upload")
async def upload_invoice_file(file: UploadFile = File(...)):
    UPLOAD_DIR = "uploads"
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
    
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"file_url": f"/uploads/{unique_filename}"}


@router.post("", response_model=SaleOut, status_code=status.HTTP_201_CREATED)
def create_sale(payload: SaleCreate, db: Session = Depends(get_db)):
    po = db.get(PurchaseOrder, payload.po_id)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found.")

    invoice_number = payload.invoice_number or generate_invoice_number(db)

    sale = Sale(
        po_id=payload.po_id,
        po_number=payload.po_number,
        invoice_number=invoice_number,
        client_name=payload.client_name,
        project=payload.project,
        subtotal=payload.subtotal,
        gst_amount=payload.gst_amount,
        freight=payload.freight,
        grand_total=payload.grand_total,
        payment_status=payload.payment_status,
        payment_note=payload.payment_note,
        invoice_url=payload.invoice_url,
        e_way_bill_url=payload.e_way_bill_url,
        dispatch_from=payload.dispatch_from,
        ship_to=payload.ship_to,
        bill_to=payload.bill_to,
        dispatched_through=payload.dispatched_through,
        e_way_bill_no=payload.e_way_bill_no,
        buyers_order_no=payload.buyers_order_no,
        payment_terms=payload.payment_terms,
        hsn_code=payload.hsn_code,
        created_by=payload.created_by,
    )
    db.add(sale)
    db.flush()

    for item_data in payload.items:
        sale_item = SaleItem(
            sale_id=sale.id,
            line_item_id=item_data.line_item_id,
            item=item_data.item,
            uom=item_data.uom,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            gst_rate=item_data.gst_rate,
            subtotal=item_data.subtotal,
            gst_amount=item_data.gst_amount,
            total_amount=item_data.total_amount,
        )
        db.add(sale_item)

        # Update delivery tracking
        po.delivered_quantity += item_data.quantity
        if item_data.line_item_id:
            li = db.get(POLineItem, item_data.line_item_id)
            if li:
                li.delivered_quantity += item_data.quantity

    activity = SaleActivity(
        sale_id=sale.id,
        action="Sale Created",
        note=payload.payment_note,
        payment_status=payload.payment_status,
        by=payload.created_by,
    )
    db.add(activity)
    db.commit()
    db.refresh(sale)
    return sale


@router.get("/{sale_id}", response_model=SaleOut)
def get_sale(sale_id: int, db: Session = Depends(get_db)):
    sale = db.get(Sale, sale_id)
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found.")
    return sale


@router.put("/{sale_id}", response_model=SaleOut)
def update_sale(sale_id: int, payload: SaleUpdate, db: Session = Depends(get_db)):
    sale = db.get(Sale, sale_id)
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found.")

    updates = payload.model_dump(exclude_unset=True)
    updated_by = updates.pop("updated_by", None)

    for field, value in updates.items():
        setattr(sale, field, value)

    sale.updated_by = updated_by
    sale.updated_at = datetime.utcnow()

    if "payment_status" in updates:
        activity = SaleActivity(
            sale_id=sale.id,
            action="Payment Status Updated",
            note=payload.payment_note,
            payment_status=str(updates.get("payment_status", "")),
            by=updated_by,
        )
        db.add(activity)

    db.commit()
    db.refresh(sale)
    return sale


@router.delete("/{sale_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sale(sale_id: int, db: Session = Depends(get_db)):
    sale = db.get(Sale, sale_id)
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found.")

    po = db.get(PurchaseOrder, sale.po_id)
    
    # Rollback quantities for all items in this sale
    for item in sale.items:
        if po:
            po.delivered_quantity = max(0, po.delivered_quantity - item.quantity)
        if item.line_item_id:
            li = db.get(POLineItem, item.line_item_id)
            if li:
                li.delivered_quantity = max(0, li.delivered_quantity - item.quantity)

    db.delete(sale)
    db.commit()


@router.post("/{sale_id}/activities", response_model=SaleActivityOut, status_code=status.HTTP_201_CREATED)
def add_activity(sale_id: int, payload: SaleActivityCreate, db: Session = Depends(get_db)):
    sale = db.get(Sale, sale_id)
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found.")
    activity = SaleActivity(
        sale_id=sale_id,
        action=payload.action,
        note=payload.note,
        payment_status=payload.payment_status,
        by=payload.by,
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity

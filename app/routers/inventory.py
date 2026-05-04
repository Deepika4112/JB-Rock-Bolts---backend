from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.database import get_db
from app.models.models import Product, Sale
from app.schemas.product import ProductCreate, ProductUpdate, ProductOut
from app.utils.helpers import derive_inventory_status

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])


def _to_out(product: Product, sales_count: int = 0) -> ProductOut:
    return ProductOut(
        id=product.id,
        name=product.name,
        quantity=product.quantity,
        status=product.status,
        sales_count=sales_count,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


@router.get("", response_model=List[ProductOut])
def list_inventory(db: Session = Depends(get_db)):
    products = db.query(Product).order_by(Product.name).all()
    sales_counts = (
        db.query(Sale.item, func.count(Sale.id).label("cnt"))
        .group_by(Sale.item)
        .all()
    )
    count_map = {r.item: r.cnt for r in sales_counts}
    return [_to_out(p, count_map.get(p.name, 0)) for p in products]


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    existing = db.query(Product).filter(Product.name == payload.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Product '{payload.name}' already exists.",
        )
    auto_status = payload.status or derive_inventory_status(payload.quantity)
    product = Product(name=payload.name, quantity=payload.quantity, status=auto_status)
    db.add(product)
    db.commit()
    db.refresh(product)
    return _to_out(product)


@router.put("/{product_id}", response_model=ProductOut)
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    if payload.quantity is not None:
        product.quantity = payload.quantity
        product.status = payload.status or derive_inventory_status(payload.quantity)
    elif payload.status is not None:
        product.status = payload.status

    db.commit()
    db.refresh(product)
    return _to_out(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    db.delete(product)
    db.commit()

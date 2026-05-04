from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.models.models import Record
from app.schemas.reports import ReportOut, ReportRow

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("", response_model=ReportOut)
def get_report(
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    product: Optional[str] = None,
    client: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(Record)
    if from_date:
        q = q.filter(Record.date >= from_date)
    if to_date:
        q = q.filter(Record.date <= to_date)
    if product and product.lower() != "all":
        q = q.filter(Record.product.ilike(f"%{product}%"))
    if client and client.lower() != "all":
        q = q.filter(Record.client_name.ilike(f"%{client}%"))

    records = q.order_by(Record.date.desc()).limit(limit).all()

    total_revenue = sum(r.price for r in records)
    record_count = len(records)
    avg_order_value = total_revenue / record_count if record_count else 0

    rows = [
        ReportRow(
            id=r.id,
            date=r.date.strftime("%d %b %Y") if r.date else "",
            client_name=r.client_name,
            product=r.product,
            location=r.location,
            po_number=r.po_number,
            invoice_number=r.invoice_number,
            price=r.price,
            payment_status=r.payment_status,
            delivery_status=r.delivery_status,
        )
        for r in records
    ]

    return ReportOut(
        rows=rows,
        total_revenue=round(total_revenue, 2),
        record_count=record_count,
        avg_order_value=round(avg_order_value, 2),
    )

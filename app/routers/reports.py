from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.models.models import Record, PurchaseOrder, Sale
from app.schemas.reports import ReportOut, ReportRow, FulfillmentReportOut, FulfillmentReportRow

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
    q = db.query(Sale)
    if from_date:
        q = q.filter(Sale.created_at >= from_date)
    if to_date:
        # Include the entire day for to_date
        from datetime import time
        to_date_end = datetime.combine(to_date.date(), time(23, 59, 59))
        q = q.filter(Sale.created_at <= to_date_end)
    if product:
        from app.models.models import SaleItem
        q = q.join(Sale.items).filter(SaleItem.item.ilike(f"%{product}%"))
    if client and client.lower() != "all":
        q = q.filter(Sale.client_name.ilike(f"%{client}%"))

    sales = q.order_by(Sale.created_at.desc()).limit(limit).all()

    total_revenue = sum(s.grand_total for s in sales)
    record_count = len(sales)
    avg_order_value = total_revenue / record_count if record_count else 0

    rows = [
        ReportRow(
            id=s.id,
            date=s.created_at.strftime("%d-%m-%Y") if s.created_at else "",
            client_name=s.client_name,
            product=s.items_display,
            location=s.project or "—",
            po_number=s.po_number,
            invoice_number=s.invoice_number,
            e_way_bill_no=s.e_way_bill_no,
            price=s.grand_total,
            payment_status=s.payment_status.value if hasattr(s.payment_status, 'value') else str(s.payment_status),
            delivery_status="Dispatched",
        )
        for s in sales
    ]

    return ReportOut(
        rows=rows,
        total_revenue=round(total_revenue, 2),
        record_count=record_count,
        avg_order_value=round(avg_order_value, 2),
    )


@router.get("/fulfillment", response_model=FulfillmentReportOut)
def get_fulfillment_report(
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    client: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(PurchaseOrder)
    if from_date:
        q = q.filter(PurchaseOrder.created_at >= from_date)
    if to_date:
        from datetime import time
        to_date_end = datetime.combine(to_date.date(), time(23, 59, 59))
        q = q.filter(PurchaseOrder.created_at <= to_date_end)
    if client and client.lower() != "all":
        q = q.filter(PurchaseOrder.client_name.ilike(f"%{client}%"))

    orders = q.order_by(PurchaseOrder.created_at.desc()).all()

    rows = [
        FulfillmentReportRow(
            id=o.id,
            date=o.created_at.strftime("%d-%m-%Y") if o.created_at else "—",
            client_name=o.client_name,
            project=o.project or "—",
            item=o.items_display,
            total_required=o.total_quantity,
            delivered=o.delivered_quantity,
            pending=max(0, o.total_quantity - o.delivered_quantity),
            uom=o.uom or "Nos",
        )
        for o in orders
    ]

    return FulfillmentReportOut(rows=rows)

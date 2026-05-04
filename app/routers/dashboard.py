from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.models import Record, PurchaseOrder, Client, PaymentStatus, DeliveryStatus
from app.schemas.dashboard import DashboardStats, ChartData, ChartDataPoint, MonthlyTrend, RecentSale
from typing import List
from datetime import datetime

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_stats(db: Session = Depends(get_db)):
    total_revenue = db.query(func.sum(Record.price)).scalar() or 0
    total_orders = db.query(func.count(Record.id)).scalar() or 0
    total_clients = db.query(func.count(func.distinct(Record.client_name))).scalar() or 0
    delivered_orders = db.query(func.count(Record.id)).filter(
        Record.delivery_status == DeliveryStatus.DELIVERED
    ).scalar() or 0
    pending_payments = db.query(func.count(Record.id)).filter(
        Record.payment_status == PaymentStatus.PENDING
    ).scalar() or 0

    return DashboardStats(
        total_revenue=total_revenue,
        total_orders=total_orders,
        total_clients=total_clients,
        delivered_orders=delivered_orders,
        pending_payments=pending_payments,
    )


@router.get("/charts", response_model=ChartData)
def get_charts(db: Session = Depends(get_db)):
    product_rows = (
        db.query(Record.product, func.sum(Record.price).label("total"))
        .group_by(Record.product)
        .order_by(func.sum(Record.price).desc())
        .limit(10)
        .all()
    )
    sales_by_product = [ChartDataPoint(name=r.product, value=r.total or 0) for r in product_rows]

    payment_rows = (
        db.query(Record.payment_status, func.count(Record.id).label("cnt"))
        .group_by(Record.payment_status)
        .all()
    )
    payment_status = [ChartDataPoint(name=r.payment_status, value=r.cnt or 0) for r in payment_rows]

    monthly_rows = (
        db.query(
            func.date_format(Record.date, "%b %Y").label("month"),
            func.sum(Record.price).label("revenue"),
            func.count(Record.id).label("orders"),
        )
        .group_by(func.date_format(Record.date, "%b %Y"), func.date_format(Record.date, "%Y%m"))
        .order_by(func.date_format(Record.date, "%Y%m"))
        .limit(12)
        .all()
    )
    monthly_trend = [
        MonthlyTrend(month=r.month, revenue=r.revenue or 0, orders=r.orders or 0)
        for r in monthly_rows
    ]

    return ChartData(
        sales_by_product=sales_by_product,
        payment_status=payment_status,
        monthly_trend=monthly_trend,
    )


@router.get("/recent-sales", response_model=List[RecentSale])
def get_recent_sales(limit: int = 6, db: Session = Depends(get_db)):
    rows = (
        db.query(Record)
        .order_by(Record.date.desc())
        .limit(limit)
        .all()
    )
    return [
        RecentSale(
            id=r.id,
            client_name=r.client_name,
            product=r.product,
            price=r.price,
            payment_status=r.payment_status,
            delivery_status=r.delivery_status,
            date=r.date.isoformat() if r.date else "",
            invoice_number=r.invoice_number,
        )
        for r in rows
    ]

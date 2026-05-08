from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.models import Sale, PurchaseOrder, Client, PaymentStatus
from app.schemas.dashboard import DashboardStats, ChartData, ChartDataPoint, MonthlyTrend, RecentSale
from typing import List

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_stats(db: Session = Depends(get_db)):
    # Total revenue from all sales (dispatches)
    total_revenue = db.query(func.sum(Sale.grand_total)).scalar() or 0
    # Total number of dispatches
    total_orders = db.query(func.count(Sale.id)).scalar() or 0
    # Total unique clients who have made a purchase
    total_clients = db.query(func.count(func.distinct(Sale.client_name))).scalar() or 0
    # Every sale entry represents a delivery/dispatch
    delivered_orders = total_orders
    # Payments that are not fully paid
    pending_payments = db.query(func.count(Sale.id)).filter(
        Sale.payment_status.in_([PaymentStatus.PENDING, PaymentStatus.PARTIAL])
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
    # Sales by Product (item)
    product_rows = (
        db.query(Sale.item, func.sum(Sale.grand_total).label("total"))
        .group_by(Sale.item)
        .order_by(func.sum(Sale.grand_total).desc())
        .limit(10)
        .all()
    )
    sales_by_product = [ChartDataPoint(name=r.item, value=r.total or 0) for r in product_rows]

    # Payment Status distribution
    payment_rows = (
        db.query(Sale.payment_status, func.count(Sale.id).label("cnt"))
        .group_by(Sale.payment_status)
        .all()
    )
    payment_status = [ChartDataPoint(name=str(r.payment_status.value), value=r.cnt or 0) for r in payment_rows]

    # Monthly Trend
    monthly_rows = (
        db.query(
            func.date_format(Sale.created_at, "%b %Y").label("month"),
            func.sum(Sale.grand_total).label("revenue"),
            func.count(Sale.id).label("orders"),
        )
        .group_by(func.date_format(Sale.created_at, "%b %Y"))
        .order_by(func.min(Sale.created_at))
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
        db.query(Sale)
        .order_by(Sale.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        RecentSale(
            id=r.id,
            client_name=r.client_name,
            product=r.item,
            price=r.grand_total,
            payment_status=str(r.payment_status.value),
            delivery_status="Delivered",
            date=r.created_at.isoformat() if r.created_at else "",
            invoice_number=r.invoice_number,
        )
        for r in rows
    ]

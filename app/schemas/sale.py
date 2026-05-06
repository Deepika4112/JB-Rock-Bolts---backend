from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.models.models import PaymentStatus


class SaleActivityCreate(BaseModel):
    action: str
    note: Optional[str] = None
    payment_status: Optional[str] = None
    by: Optional[str] = None


class SaleActivityOut(BaseModel):
    id: int
    sale_id: int
    action: str
    note: Optional[str]
    payment_status: Optional[str]
    at: datetime
    by: Optional[str]

    model_config = {"from_attributes": True}


class SaleCreate(BaseModel):
    po_id: int
    po_number: str
    invoice_number: Optional[str] = None
    client_name: str
    item: str
    project: Optional[str] = None
    uom: str = "Nos"
    dispatched_qty: float
    total_qty: float
    previous_delivered: float = 0
    unit_price: float = 0
    gst_rate: float = 18
    freight: float = 0
    payment_status: PaymentStatus = PaymentStatus.PENDING
    payment_note: Optional[str] = None
    invoice_url: Optional[str] = None
    dispatch_from: Optional[str] = None
    ship_to: Optional[str] = None
    bill_to: Optional[str] = None
    dispatched_through: Optional[str] = None
    buyers_order_no: Optional[str] = None
    payment_terms: Optional[str] = None
    created_by: Optional[str] = None


class SaleUpdate(BaseModel):
    payment_status: Optional[PaymentStatus] = None
    payment_note: Optional[str] = None
    dispatched_qty: Optional[float] = None
    invoice_url: Optional[str] = None
    dispatch_from: Optional[str] = None
    ship_to: Optional[str] = None
    bill_to: Optional[str] = None
    dispatched_through: Optional[str] = None
    buyers_order_no: Optional[str] = None
    payment_terms: Optional[str] = None
    updated_by: Optional[str] = None


class SaleOut(BaseModel):
    id: int
    po_id: int
    po_number: str
    invoice_number: Optional[str]
    client_name: str
    item: str
    project: Optional[str]
    uom: str
    dispatched_qty: float
    total_qty: float
    previous_delivered: float
    unit_price: float
    gst_rate: float
    gst_amount: float
    freight: float
    subtotal: float
    grand_total: float
    payment_status: PaymentStatus
    payment_note: Optional[str]
    created_at: datetime
    created_by: Optional[str]
    updated_at: datetime
    updated_by: Optional[str]
    invoice_url: Optional[str]
    dispatch_from: Optional[str]
    ship_to: Optional[str]
    bill_to: Optional[str]
    dispatched_through: Optional[str]
    buyers_order_no: Optional[str]
    payment_terms: Optional[str]
    activities: List[SaleActivityOut] = []

    model_config = {"from_attributes": True}

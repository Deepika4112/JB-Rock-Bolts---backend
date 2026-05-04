from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PurchaseOrderCreate(BaseModel):
    client_name: str
    po_number: str
    item: str
    uom: str = "Nos"
    project: Optional[str] = None
    project_id: Optional[int] = None
    location: Optional[str] = None
    total_quantity: float
    unit_price: float = 0
    gst: Optional[str] = "18"
    freight: float = 0
    payment_terms: Optional[str] = None
    validity_date: Optional[datetime] = None
    delivery_date: Optional[datetime] = None
    created_by: Optional[str] = None


class PurchaseOrderUpdate(BaseModel):
    client_name: Optional[str] = None
    item: Optional[str] = None
    uom: Optional[str] = None
    project: Optional[str] = None
    project_id: Optional[int] = None
    location: Optional[str] = None
    total_quantity: Optional[float] = None
    delivered_quantity: Optional[float] = None
    unit_price: Optional[float] = None
    gst: Optional[str] = None
    freight: Optional[float] = None
    payment_terms: Optional[str] = None
    validity_date: Optional[datetime] = None
    delivery_date: Optional[datetime] = None
    last_updated_by: Optional[str] = None


class PurchaseOrderOut(BaseModel):
    id: int
    client_name: str
    po_number: str
    item: str
    uom: str
    project: Optional[str]
    project_id: Optional[int]
    location: Optional[str]
    total_quantity: float
    delivered_quantity: float
    pending_quantity: float
    unit_price: float
    gst: Optional[str]
    gst_rate: float
    freight: float
    payment_terms: Optional[str]
    validity_date: Optional[datetime]
    delivery_date: Optional[datetime]
    delivery_status: str
    subtotal: float
    gst_amount: float
    grand_total: float
    created_at: datetime
    created_by: Optional[str]
    last_opened_at: Optional[datetime]
    last_opened_by: Optional[str]
    last_updated_at: Optional[datetime]
    last_updated_by: Optional[str]

    model_config = {"from_attributes": True}

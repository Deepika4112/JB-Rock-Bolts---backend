from pydantic import BaseModel, computed_field
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


class SaleItemCreate(BaseModel):
    line_item_id: Optional[int] = None
    item: str
    uom: str = "Nos"
    quantity: float
    unit_price: float
    gst_rate: float = 18
    subtotal: float
    gst_amount: float
    total_amount: float

class SaleItemOut(BaseModel):
    id: int
    line_item_id: Optional[int]
    item: str
    uom: str
    quantity: float
    unit_price: float
    gst_rate: float
    subtotal: float
    gst_amount: float
    total_amount: float

    model_config = {"from_attributes": True}

class SaleCreate(BaseModel):
    po_id: int
    po_number: str
    invoice_number: Optional[str] = None
    client_name: str
    project: Optional[str] = None
    items: List[SaleItemCreate]
    subtotal: float
    gst_amount: float
    freight: float = 0
    grand_total: float
    payment_status: PaymentStatus = PaymentStatus.PENDING
    payment_note: Optional[str] = None
    invoice_url: Optional[str] = None
    e_way_bill_url: Optional[str] = None
    dispatch_from: Optional[str] = None
    ship_to: Optional[str] = None
    bill_to: Optional[str] = None
    dispatched_through: Optional[str] = None
    e_way_bill_no: Optional[str] = None
    buyers_order_no: Optional[str] = None
    payment_terms: Optional[str] = None
    hsn_code: Optional[str] = None
    created_by: Optional[str] = None

class SaleUpdate(BaseModel):
    invoice_number: Optional[str] = None
    payment_status: Optional[PaymentStatus] = None
    payment_note: Optional[str] = None
    invoice_url: Optional[str] = None
    e_way_bill_url: Optional[str] = None
    dispatch_from: Optional[str] = None
    ship_to: Optional[str] = None
    bill_to: Optional[str] = None
    dispatched_through: Optional[str] = None
    e_way_bill_no: Optional[str] = None
    buyers_order_no: Optional[str] = None
    payment_terms: Optional[str] = None
    hsn_code: Optional[str] = None
    freight: Optional[float] = None
    updated_by: Optional[str] = None

class SaleOut(BaseModel):
    id: int
    po_id: int
    po_number: str
    invoice_number: Optional[str]
    client_name: str
    project: Optional[str]
    subtotal: float
    gst_amount: float
    freight: float
    grand_total: float
    payment_status: PaymentStatus
    payment_note: Optional[str]
    created_at: datetime
    created_by: Optional[str]
    updated_at: datetime
    updated_by: Optional[str]
    invoice_url: Optional[str]
    e_way_bill_url: Optional[str]
    dispatch_from: Optional[str]
    ship_to: Optional[str]
    bill_to: Optional[str]
    dispatched_through: Optional[str]
    e_way_bill_no: Optional[str]
    buyers_order_no: Optional[str]
    payment_terms: Optional[str]
    hsn_code: Optional[str]
    items: List[SaleItemOut] = []
    activities: List[SaleActivityOut] = []

    model_config = {"from_attributes": True}

    @computed_field
    @property
    def item(self) -> str:
        if self.items:
            return ", ".join(i.item for i in self.items)
        return ""

    @computed_field
    @property
    def dispatched_qty(self) -> float:
        return sum(i.quantity for i in self.items)

    @computed_field
    @property
    def unit_price(self) -> float:
        return self.items[0].unit_price if self.items else 0

    @computed_field
    @property
    def gst_rate(self) -> float:
        return self.items[0].gst_rate if self.items else 0

    @computed_field
    @property
    def uom(self) -> str:
        return self.items[0].uom if self.items else "Nos"

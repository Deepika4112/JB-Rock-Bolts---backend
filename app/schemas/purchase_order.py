from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class POLineItemBase(BaseModel):
    item: str
    quantity: float = 0
    delivered_quantity: float = 0
    uom: str = "Nos"
    unit_price: float = 0

    @property
    def pending_quantity(self) -> float:
        return max(0, self.quantity - self.delivered_quantity)

class POLineItemCreate(POLineItemBase):
    pass

class POLineItemOut(POLineItemBase):
    id: int
    pending_quantity: float = 0
    model_config = {"from_attributes": True}

class PurchaseOrderBase(BaseModel):
    client_name: str
    po_number: str
    project: Optional[str] = None
    project_id: Optional[int] = None
    location: Optional[str] = None
    gst: Optional[str] = "18"
    freight: float = 0
    payment_terms: Optional[str] = None
    validity_date: Optional[datetime] = None
    file_url: Optional[str] = None

class PurchaseOrderCreate(PurchaseOrderBase):
    created_by: Optional[str] = None
    line_items: List[POLineItemCreate] = []

class PurchaseOrderUpdate(BaseModel):
    client_name: Optional[str] = None
    po_number: Optional[str] = None
    project: Optional[str] = None
    project_id: Optional[int] = None
    location: Optional[str] = None
    gst: Optional[str] = None
    freight: Optional[float] = None
    payment_terms: Optional[str] = None
    validity_date: Optional[datetime] = None
    file_url: Optional[str] = None
    last_updated_by: Optional[str] = None
    line_items: Optional[List[POLineItemCreate]] = None

class PurchaseOrderOut(PurchaseOrderBase):
    id: int
    item: Optional[str] = ""
    uom: Optional[str] = "Nos"
    total_quantity: float = 0
    delivered_quantity: float = 0
    pending_quantity: float = 0
    unit_price: float = 0
    gst_rate: float = 0
    delivery_status: str = "Not Delivered"
    subtotal: float = 0
    gst_amount: float = 0
    grand_total: float = 0
    created_at: datetime
    created_by: Optional[str] = None
    last_opened_at: Optional[datetime] = None
    last_opened_by: Optional[str] = None
    last_updated_at: Optional[datetime] = None
    last_updated_by: Optional[str] = None
    line_items: List[POLineItemOut] = []

    model_config = {"from_attributes": True}

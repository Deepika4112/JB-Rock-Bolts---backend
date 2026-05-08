from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class ReportFilter(BaseModel):
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    product: Optional[str] = None
    client: Optional[str] = None


class ReportRow(BaseModel):
    id: int
    date: str
    client_name: str
    product: str
    location: Optional[str]
    po_number: Optional[str]
    invoice_number: Optional[str]
    e_way_bill_no: Optional[str] = None
    price: float
    payment_status: str
    delivery_status: str


class ReportOut(BaseModel):
    rows: List[ReportRow]
    total_revenue: float
    record_count: int
    avg_order_value: float


class FulfillmentReportRow(BaseModel):
    id: int
    date: str
    client_name: str
    project: str
    item: str
    total_required: float
    delivered: float
    pending: float
    uom: str


class FulfillmentReportOut(BaseModel):
    rows: List[FulfillmentReportRow]

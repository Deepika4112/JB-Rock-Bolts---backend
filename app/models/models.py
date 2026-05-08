from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, Boolean,
    ForeignKey, Enum, func,
)
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class PaymentStatus(str, enum.Enum):
    PENDING = "Pending"
    PARTIAL = "Partial"
    PAID = "Paid"


class DeliveryStatus(str, enum.Enum):
    PENDING = "Pending"
    DELIVERED = "Delivered"


class InventoryStatus(str, enum.Enum):
    IN_STOCK = "In Stock"
    LOW_STOCK = "Low Stock"
    OUT_OF_STOCK = "Out of Stock"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    location = Column(String(100), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    purchase_orders = relationship("PurchaseOrder", back_populates="client_rel")
    records = relationship("Record", back_populates="client_rel")
    projects = relationship("Project", back_populates="client_rel", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(300), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    client_rel = relationship("Client", back_populates="projects")
    purchase_orders = relationship("PurchaseOrder", back_populates="project_rel")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(300), nullable=False, unique=True, index=True)
    quantity = Column(Integer, default=0, nullable=False)
    status = Column(
        Enum(InventoryStatus),
        default=InventoryStatus.IN_STOCK,
        nullable=False,
    )
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String(200), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    po_number = Column(String(100), nullable=False, unique=True, index=True)
    item = Column(String(300), nullable=True, default="")
    uom = Column(String(50), nullable=False, default="Nos")
    project = Column(String(300), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    location = Column(String(100), nullable=True)
    total_quantity = Column(Float, nullable=False, default=0)
    delivered_quantity = Column(Float, nullable=False, default=0)
    unit_price = Column(Float, nullable=False, default=0)
    gst = Column(String(20), nullable=True, default="18")
    freight = Column(Float, nullable=False, default=0)
    payment_terms = Column(String(100), nullable=True)
    validity_date = Column(DateTime, nullable=True)
    file_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(100), nullable=True)
    last_opened_at = Column(DateTime, nullable=True)
    last_opened_by = Column(String(100), nullable=True)
    last_updated_at = Column(DateTime, nullable=True)
    last_updated_by = Column(String(100), nullable=True)

    client_rel = relationship("Client", back_populates="purchase_orders")
    project_rel = relationship("Project", back_populates="purchase_orders")
    sales = relationship("Sale", back_populates="purchase_order")
    line_items = relationship("POLineItem", back_populates="purchase_order", cascade="all, delete-orphan", order_by="POLineItem.id")

    @property
    def pending_quantity(self) -> float:
        return max(0, self.total_quantity - self.delivered_quantity)

    @property
    def delivery_status(self) -> str:
        if self.delivered_quantity <= 0:
            return DeliveryStatus.PENDING
        elif self.delivered_quantity >= self.total_quantity:
            return DeliveryStatus.DELIVERED
        return "Partial"

    @property
    def gst_rate(self) -> float:
        if not self.gst:
            return 18.0
        cleaned = str(self.gst).replace("%", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return 18.0

    @property
    def subtotal(self) -> float:
        if self.line_items:
            return sum(li.quantity * li.unit_price for li in self.line_items)
        return self.total_quantity * self.unit_price

    @property
    def gst_amount(self) -> float:
        return self.subtotal * self.gst_rate / 100

    @property
    def grand_total(self) -> float:
        return self.subtotal + self.gst_amount + self.freight

    @property
    def items_display(self) -> str:
        """Comma-separated item names for display."""
        if self.line_items:
            return ", ".join(li.item for li in self.line_items)
        return self.item or ""


class POLineItem(Base):
    __tablename__ = "po_line_items"

    id = Column(Integer, primary_key=True, index=True)
    po_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    item = Column(String(300), nullable=False)
    quantity = Column(Float, nullable=False, default=0)
    delivered_quantity = Column(Float, nullable=False, default=0)
    uom = Column(String(50), nullable=False, default="Nos")
    unit_price = Column(Float, nullable=False, default=0)

    purchase_order = relationship("PurchaseOrder", back_populates="line_items")


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    po_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    po_number = Column(String(100), nullable=False, index=True)
    invoice_number = Column(String(50), nullable=True, unique=True, index=True)
    client_name = Column(String(200), nullable=False, index=True)
    project = Column(String(300), nullable=True)
    
    # Financials (Aggregate)
    subtotal = Column(Float, nullable=False, default=0)
    gst_amount = Column(Float, nullable=False, default=0)
    freight = Column(Float, nullable=False, default=0)
    grand_total = Column(Float, nullable=False, default=0)
    
    payment_status = Column(
        Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False
    )
    payment_note = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(100), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    updated_by = Column(String(100), nullable=True)
    invoice_url = Column(String(500), nullable=True)
    e_way_bill_url = Column(String(500), nullable=True)
    dispatch_from = Column(Text, nullable=True)
    ship_to = Column(Text, nullable=True)
    bill_to = Column(Text, nullable=True)
    dispatched_through = Column(String(200), nullable=True)
    e_way_bill_no = Column(String(100), nullable=True)
    buyers_order_no = Column(String(100), nullable=True)
    payment_terms = Column(String(200), nullable=True)
    hsn_code = Column(String(50), nullable=True)
    
    @property
    def items_display(self) -> str:
        if self.items:
            return ", ".join(i.item for i in self.items)
        return ""

    purchase_order = relationship("PurchaseOrder", back_populates="sales")
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
    activities = relationship(
        "SaleActivity", back_populates="sale", cascade="all, delete-orphan"
    )

class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    line_item_id = Column(Integer, ForeignKey("po_line_items.id"), nullable=True)
    
    item = Column(String(300), nullable=False)
    uom = Column(String(50), nullable=False, default="Nos")
    quantity = Column(Float, nullable=False, default=0)
    unit_price = Column(Float, nullable=False, default=0)
    gst_rate = Column(Float, nullable=False, default=18)
    
    # Pre-calculated totals for this item
    subtotal = Column(Float, nullable=False, default=0)
    gst_amount = Column(Float, nullable=False, default=0)
    total_amount = Column(Float, nullable=False, default=0)

    sale = relationship("Sale", back_populates="items")


class SaleActivity(Base):
    __tablename__ = "sale_activities"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    action = Column(String(200), nullable=False)
    note = Column(Text, nullable=True)
    payment_status = Column(String(50), nullable=True)
    at = Column(DateTime, server_default=func.now())
    by = Column(String(100), nullable=True)

    sale = relationship("Sale", back_populates="activities")


class Record(Base):
    """Legacy/dashboard sales record (mirrors frontend mock data shape)."""

    __tablename__ = "records"

    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String(200), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    product = Column(String(300), nullable=False, index=True)
    price = Column(Float, nullable=False, default=0)
    location = Column(String(100), nullable=True)
    payment_status = Column(
        Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False
    )
    delivery_status = Column(
        Enum(DeliveryStatus), default=DeliveryStatus.PENDING, nullable=False
    )
    po_number = Column(String(100), nullable=True)
    invoice_number = Column(String(50), nullable=True)
    date = Column(DateTime, server_default=func.now())
    created_at = Column(DateTime, server_default=func.now())

    client_rel = relationship("Client", back_populates="records")

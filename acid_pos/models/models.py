"""
نماذج البيانات (Models)
========================
مجرد أوصاف لشكل البيانات (dataclasses) يسهل التعامل معها في الكود
بدل التعامل مع صفوف قاعدة البيانات الخام (sqlite3.Row) في كل مكان.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Employee:
    id: Optional[int]
    name: str
    username: str
    role: str  # 'manager' or 'employee'
    is_active: bool = True
    permissions: set = field(default_factory=set)

    @property
    def is_manager(self) -> bool:
        return self.role == "manager"


@dataclass
class Product:
    id: Optional[int]
    name: str
    current_quantity_kg: float
    alert_threshold_kg: float
    is_active: bool = True

    @property
    def is_below_alert(self) -> bool:
        return self.current_quantity_kg <= self.alert_threshold_kg


@dataclass
class DailyPrice:
    id: Optional[int]
    product_id: int
    price_per_kg: float
    date: str
    set_by: Optional[int] = None


@dataclass
class Customer:
    id: Optional[int]
    name: str
    phone: Optional[str]
    total_debt: float = 0.0
    code: Optional[str] = None


@dataclass
class Invoice:
    id: Optional[int]
    date_time: str
    customer_id: Optional[int]
    employee_id: int
    is_printed: bool
    is_credit: bool
    subtotal_amount: float
    discount_amount: float
    total_amount: float
    is_deleted: bool = False
    notes: Optional[str] = None
    items: list = field(default_factory=list)


@dataclass
class InvoiceItem:
    id: Optional[int]
    invoice_id: int
    product_id: int
    quantity_kg: float
    price_per_kg_at_sale: float
    purchase_price_per_kg: Optional[float]
    line_total: float


@dataclass
class Payment:
    id: Optional[int]
    customer_id: int
    amount: float
    date: str
    received_by: Optional[int] = None
    notes: Optional[str] = None


@dataclass
class StockMovement:
    id: Optional[int]
    product_id: int
    movement_type: str  # 'in' or 'out'
    quantity_kg: float
    balance_after_kg: float
    date: str
    related_invoice_id: Optional[int] = None
    purchase_price_per_kg: Optional[float] = None
    notes: Optional[str] = None

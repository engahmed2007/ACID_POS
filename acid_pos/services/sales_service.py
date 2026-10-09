"""
خدمة البيع والفواتير
=======================
إنشاء فاتورة بأكتر من صنف، خصم المخزون تلقائي، تحديث مديونية العميل
لو الفاتورة آجلة، والبحث في الفواتير القديمة.
"""

from database.db_manager import db
from models.models import Invoice, InvoiceItem
from services import inventory_service
from services.customer_service import add_debt_to_customer


def get_next_invoice_number() -> int:
    """
    رقم الفاتورة المتوقع للفاتورة القادمة (لعرضه في شاشة البيع قبل
    الحفظ). الرقم الفعلي بيتحدد وقت الحفظ نفسه من AUTOINCREMENT.
    """
    row = db.fetch_one("SELECT COALESCE(MAX(id), 0) as max_id FROM invoices")
    return row["max_id"] + 1


class SaleItemInput:
    """صنف واحد في الفاتورة قبل الحفظ (بيانات مؤقتة قادمة من شاشة البيع)."""

    def __init__(self, product_id: int, quantity_kg: float, price_per_kg: float):
        self.product_id = product_id
        self.quantity_kg = quantity_kg
        self.price_per_kg = price_per_kg  # ممكن يكون معدّل يدوي عن السعر اليومي

    @property
    def line_total(self) -> float:
        return round(self.quantity_kg * self.price_per_kg, 2)


def create_invoice(
    employee_id: int,
    items: list[SaleItemInput],
    customer_id: int = None,
    is_credit: bool = False,
    discount_amount: float = 0.0,
    notes: str = None,
) -> int:
    """
    إنشاء فاتورة جديدة:
    - بيتأكد إن الكمية متاحة لكل صنف قبل ما يبدأ يسجل حاجة
    - يخصم من المخزون
    - يطبّق الخصم (لو موجود) على إجمالي الفاتورة
    - لو آجل، يضيف المبلغ (بعد الخصم) لمديونية العميل
    """
    if not items:
        raise ValueError("لازم تضيف صنف واحد على الأقل في الفاتورة")

    if is_credit and customer_id is None:
        raise ValueError("الفاتورة الآجلة لازم تكون مربوطة بعميل")

    if discount_amount < 0:
        raise ValueError("قيمة الخصم لا يمكن أن تكون سالبة")

    # تأكد الكمية متاحة لكل الأصناف الأول (قبل أي تعديل فعلي)
    for item in items:
        product = inventory_service.get_product(item.product_id)
        if product is None:
            raise ValueError("أحد الأنواع غير موجود")
        if item.quantity_kg > product.current_quantity_kg:
            raise ValueError(
                f"الكمية المطلوبة من '{product.name}' ({item.quantity_kg} كجم) "
                f"أكبر من المتاح ({product.current_quantity_kg} كجم)"
            )

    subtotal_amount = round(sum(i.line_total for i in items), 2)

    if discount_amount > subtotal_amount:
        raise ValueError("قيمة الخصم أكبر من إجمالي الفاتورة")

    total_amount = round(subtotal_amount - discount_amount, 2)

    invoice_id = db.execute(
        """INSERT INTO invoices
           (customer_id, employee_id, is_printed, is_credit,
            subtotal_amount, discount_amount, total_amount, notes)
           VALUES (?, ?, 0, ?, ?, ?, ?, ?)""",
        (customer_id, employee_id, int(is_credit), subtotal_amount,
         discount_amount, total_amount, notes),
    )

    for item in items:
        purchase_price = inventory_service.get_last_purchase_price(item.product_id)
        db.execute(
            """INSERT INTO invoice_items
               (invoice_id, product_id, quantity_kg, price_per_kg_at_sale,
                purchase_price_per_kg, line_total)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                invoice_id,
                item.product_id,
                item.quantity_kg,
                item.price_per_kg,
                purchase_price,
                item.line_total,
            ),
        )
        inventory_service.record_stock_out(
            item.product_id, item.quantity_kg, related_invoice_id=invoice_id
        )

    if is_credit:
        add_debt_to_customer(customer_id, total_amount)

    return invoice_id


def get_invoice(invoice_id: int) -> Invoice | None:
    r = db.fetch_one(
        "SELECT * FROM invoices WHERE id = ? AND is_deleted = 0", (invoice_id,)
    )
    if r is None:
        return None
    items_rows = db.fetch_all(
        """SELECT ii.*, p.name as product_name FROM invoice_items ii
           JOIN products p ON ii.product_id = p.id
           WHERE ii.invoice_id = ?""",
        (invoice_id,),
    )
    invoice = Invoice(
        id=r["id"],
        date_time=r["date_time"],
        customer_id=r["customer_id"],
        employee_id=r["employee_id"],
        is_printed=bool(r["is_printed"]),
        is_credit=bool(r["is_credit"]),
        subtotal_amount=r["subtotal_amount"],
        discount_amount=r["discount_amount"],
        total_amount=r["total_amount"],
        is_deleted=bool(r["is_deleted"]),
        notes=r["notes"],
        items=[dict(ir) for ir in items_rows],
    )
    return invoice


def search_invoices(
    date_from: str = None,
    date_to: str = None,
    customer_name: str = None,
    invoice_id: int = None,
    employee_id: int = None,
) -> list[dict]:
    """
    بحث مرن عن الفواتير بأي تركيبة من: التاريخ (من/إلى)، اسم العميل،
    رقم الفاتورة، أو الموظف اللي عملها.
    """
    query = """
        SELECT i.id, i.date_time, i.total_amount, i.is_credit,
               c.name as customer_name, e.name as employee_name
        FROM invoices i
        LEFT JOIN customers c ON i.customer_id = c.id
        JOIN employees e ON i.employee_id = e.id
        WHERE i.is_deleted = 0
    """
    params = []
    if invoice_id is not None:
        query += " AND i.id = ?"
        params.append(invoice_id)
    if date_from:
        query += " AND date(i.date_time) >= date(?)"
        params.append(date_from)
    if date_to:
        query += " AND date(i.date_time) <= date(?)"
        params.append(date_to)
    if customer_name:
        query += " AND c.name LIKE ?"
        params.append(f"%{customer_name}%")
    if employee_id is not None:
        query += " AND i.employee_id = ?"
        params.append(employee_id)

    query += " ORDER BY i.date_time DESC"
    rows = db.fetch_all(query, tuple(params))
    return [dict(r) for r in rows]


def delete_invoice(invoice_id: int, employee_id: int, reason: str = None):
    """
    حذف منطقي فقط (soft delete) - الفاتورة بتفضل في قاعدة البيانات
    لكن مش بتظهر في البحث، والمخزون بيترجع زي ما كان.
    مسموح للمدير فقط (يتحقق منها في الشاشة قبل النداء على الدالة).
    """
    invoice = get_invoice(invoice_id)
    if invoice is None:
        raise ValueError("الفاتورة غير موجودة")

    for item in invoice.items:
        inventory_service.record_stock_in(
            item["product_id"],
            item["quantity_kg"],
            purchase_price_per_kg=item["purchase_price_per_kg"] or 0,
            notes=f"إرجاع مخزون بسبب حذف الفاتورة رقم {invoice_id}",
        )

    if invoice.is_credit and invoice.customer_id:
        add_debt_to_customer(invoice.customer_id, -invoice.total_amount)

    db.execute("UPDATE invoices SET is_deleted = 1 WHERE id = ?", (invoice_id,))
    db.execute(
        """INSERT INTO audit_log (employee_id, action, entity_type, entity_id, details)
           VALUES (?, 'DELETE_INVOICE', 'invoice', ?, ?)""",
        (employee_id, invoice_id, reason),
    )

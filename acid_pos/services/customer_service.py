"""
خدمة حسابات العملاء (آجل / ديون)
===================================
كل عميل بياخد كود مميز تلقائي وقت التسجيل (مثال: C0001) عشان تقدر
تلاقيه بسرعة بالبحث بالكود أو بالاسم، خصوصاً وقت تسجيل فاتورة آجلة.
"""

from database.db_manager import db
from models.models import Customer


def _row_to_customer(r) -> Customer:
    return Customer(
        id=r["id"], name=r["name"], phone=r["phone"],
        total_debt=r["total_debt"], code=r["code"],
    )


def list_customers() -> list[Customer]:
    rows = db.fetch_all("SELECT * FROM customers ORDER BY name")
    return [_row_to_customer(r) for r in rows]


def get_customer(customer_id: int) -> Customer | None:
    r = db.fetch_one("SELECT * FROM customers WHERE id = ?", (customer_id,))
    if r is None:
        return None
    return _row_to_customer(r)


def search_customers(query: str) -> list[Customer]:
    """بحث عن العملاء بالاسم أو بالكود (يقبل بحث جزئي وبدون حساسية لحالة الأحرف)."""
    query = (query or "").strip()
    if not query:
        return list_customers()
    like_pattern = f"%{query}%"
    rows = db.fetch_all(
        """SELECT * FROM customers
           WHERE name LIKE ? OR code LIKE ?
           ORDER BY name""",
        (like_pattern, like_pattern),
    )
    return [_row_to_customer(r) for r in rows]


def add_customer(name: str, phone: str = None) -> int:
    """
    إضافة عميل جديد. بيتولّد له كود مميز تلقائي بعد الحفظ مباشرة
    (بصيغة C0001, C0002... مبني على رقم تسلسلي العميل نفسه).
    """
    customer_id = db.execute(
        "INSERT INTO customers (name, phone, total_debt) VALUES (?, ?, 0)",
        (name, phone),
    )
    code = f"C{customer_id:04d}"
    db.execute("UPDATE customers SET code = ? WHERE id = ?", (code, customer_id))
    return customer_id


def add_debt_to_customer(customer_id: int, amount: float):
    """
    بتزود (أو تنقص لو amount سالب) مديونية العميل.
    بتستخدم عند إنشاء فاتورة آجلة، أو عند حذف فاتورة آجلة (بترجع القيمة).
    """
    db.execute(
        "UPDATE customers SET total_debt = total_debt + ? WHERE id = ?",
        (amount, customer_id),
    )


def record_payment(customer_id: int, amount: float, received_by: int, notes: str = None) -> int:
    """تسجيل دفعة جزئية أو كاملة على حساب العميل، وتحديث رصيده تلقائياً."""
    if amount <= 0:
        raise ValueError("قيمة الدفعة يجب أن تكون أكبر من صفر")

    payment_id = db.execute(
        """INSERT INTO payments (customer_id, amount, received_by, notes)
           VALUES (?, ?, ?, ?)""",
        (customer_id, amount, received_by, notes),
    )
    add_debt_to_customer(customer_id, -amount)
    return payment_id


def get_customer_payments(customer_id: int) -> list[dict]:
    rows = db.fetch_all(
        "SELECT * FROM payments WHERE customer_id = ? ORDER BY date DESC",
        (customer_id,),
    )
    return [dict(r) for r in rows]


def get_debtors_report() -> list[dict]:
    """كل العملاء اللي عليهم مديونية، مرتبين من الأكبر للأصغر."""
    rows = db.fetch_all(
        """SELECT id, code, name, phone, total_debt FROM customers
           WHERE total_debt > 0
           ORDER BY total_debt DESC"""
    )
    return [dict(r) for r in rows]

"""
خدمة إدارة المخزون
====================
كل المنطق الخاص بالمنتجات (الأنواع) وحركة المخزون (بيع/شراء) موجود هنا.
الشاشات (GUI) بتنادي الدوال دي، ومش بتكتب SQL مباشرة أبداً.
"""

from database.db_manager import db
from models.models import Product, StockMovement
from utils.formatting import format_quantity  # noqa: F401 (يعاد تصديرها للتوافق مع الاستخدام القديم)



def list_products(active_only: bool = True) -> list[Product]:
    query = "SELECT * FROM products"
    if active_only:
        query += " WHERE is_active = 1"
    query += " ORDER BY name"
    rows = db.fetch_all(query)
    return [
        Product(
            id=r["id"],
            name=r["name"],
            current_quantity_kg=r["current_quantity_kg"],
            alert_threshold_kg=r["alert_threshold_kg"],
            is_active=bool(r["is_active"]),
        )
        for r in rows
    ]


def get_product(product_id: int) -> Product | None:
    r = db.fetch_one("SELECT * FROM products WHERE id = ?", (product_id,))
    if r is None:
        return None
    return Product(
        id=r["id"],
        name=r["name"],
        current_quantity_kg=r["current_quantity_kg"],
        alert_threshold_kg=r["alert_threshold_kg"],
        is_active=bool(r["is_active"]),
    )


def add_product(name: str, alert_threshold_kg: float = 0.0) -> int:
    return db.execute(
        "INSERT INTO products (name, current_quantity_kg, alert_threshold_kg) VALUES (?, 0, ?)",
        (name, alert_threshold_kg),
    )


def update_alert_threshold(product_id: int, new_threshold_kg: float):
    db.execute(
        "UPDATE products SET alert_threshold_kg = ? WHERE id = ?",
        (new_threshold_kg, product_id),
    )


def deactivate_product(product_id: int):
    db.execute("UPDATE products SET is_active = 0 WHERE id = ?", (product_id,))


def get_low_stock_products() -> list[Product]:
    return [p for p in list_products() if p.is_below_alert]


def record_stock_in(product_id: int, quantity_kg: float, purchase_price_per_kg: float,
                     notes: str = None) -> int:
    """توريد/شراء كمية جديدة: بتزود المخزون وتسجل حركة."""
    if quantity_kg <= 0:
        raise ValueError("الكمية يجب أن تكون أكبر من صفر")

    product = get_product(product_id)
    if product is None:
        raise ValueError("الصنف غير موجود")

    new_balance = product.current_quantity_kg + quantity_kg
    db.execute(
        "UPDATE products SET current_quantity_kg = ? WHERE id = ?",
        (new_balance, product_id),
    )
    return db.execute(
        """INSERT INTO stock_movements
           (product_id, movement_type, quantity_kg, balance_after_kg,
            purchase_price_per_kg, notes)
           VALUES (?, 'in', ?, ?, ?, ?)""",
        (product_id, quantity_kg, new_balance, purchase_price_per_kg, notes),
    )


def record_stock_out(product_id: int, quantity_kg: float, related_invoice_id: int = None,
                      notes: str = None) -> int:
    """
    خصم كمية من المخزون (بيع). بترفع خطأ لو الكمية المطلوبة أكبر من المتاح
    عشان نمنع رصيد سالب.
    """
    if quantity_kg <= 0:
        raise ValueError("الكمية يجب أن تكون أكبر من صفر")

    product = get_product(product_id)
    if product is None:
        raise ValueError("الصنف غير موجود")

    if quantity_kg > product.current_quantity_kg:
        raise ValueError(
            f"الكمية المطلوبة ({quantity_kg} كجم) أكبر من المتاح في المخزون "
            f"({product.current_quantity_kg} كجم) لنوع '{product.name}'"
        )

    new_balance = product.current_quantity_kg - quantity_kg
    db.execute(
        "UPDATE products SET current_quantity_kg = ? WHERE id = ?",
        (new_balance, product_id),
    )
    return db.execute(
        """INSERT INTO stock_movements
           (product_id, movement_type, quantity_kg, balance_after_kg,
            related_invoice_id, notes)
           VALUES (?, 'out', ?, ?, ?, ?)""",
        (product_id, quantity_kg, new_balance, related_invoice_id, notes),
    )


def get_last_purchase_price(product_id: int) -> float | None:
    """آخر سعر شراء مسجل لنوع معين (يستخدم لحساب الربح التقريبي)."""
    row = db.fetch_one(
        """SELECT purchase_price_per_kg FROM stock_movements
           WHERE product_id = ? AND movement_type = 'in'
             AND purchase_price_per_kg IS NOT NULL
           ORDER BY date DESC LIMIT 1""",
        (product_id,),
    )
    return row["purchase_price_per_kg"] if row else None


def get_product_movements(product_id: int) -> list[StockMovement]:
    rows = db.fetch_all(
        "SELECT * FROM stock_movements WHERE product_id = ? ORDER BY date DESC",
        (product_id,),
    )
    return [
        StockMovement(
            id=r["id"],
            product_id=r["product_id"],
            movement_type=r["movement_type"],
            quantity_kg=r["quantity_kg"],
            balance_after_kg=r["balance_after_kg"],
            date=r["date"],
            related_invoice_id=r["related_invoice_id"],
            purchase_price_per_kg=r["purchase_price_per_kg"],
            notes=r["notes"],
        )
        for r in rows
    ]

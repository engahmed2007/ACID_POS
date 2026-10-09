"""
خدمة السعر الثابت للبيع
==========================
سعر ثابت لكل نوع تقدر تغيّره وقت ما السعر في السوق يتغير - مش لازم
تدخله كل يوم من الأول. كل تغيير بيتسجل تاريخياً (تاريخ + مين غيّره)
عشان يبقى عندك سجل بكل التعديلات اللي حصلت على السعر مع الوقت.
"""

from datetime import date as _date

from database.db_manager import db


def set_price(product_id: int, price_per_kg: float, employee_id: int) -> int:
    """تسجيل/تحديث السعر الثابت لنوع معين. يتسجل تلقائياً في سجل تاريخ الأسعار."""
    if price_per_kg <= 0:
        raise ValueError("السعر يجب أن يكون أكبر من صفر")
    return db.execute(
        """INSERT INTO daily_prices (product_id, price_per_kg, date, set_by)
           VALUES (?, ?, ?, ?)""",
        (product_id, price_per_kg, _date.today().isoformat(), employee_id),
    )


def get_current_price(product_id: int) -> float | None:
    """السعر الثابت الحالي المعمول به لهذا الصنف (آخر سعر تم تسجيله)."""
    row = db.fetch_one(
        """SELECT price_per_kg FROM daily_prices
           WHERE product_id = ? ORDER BY date DESC, id DESC LIMIT 1""",
        (product_id,),
    )
    return row["price_per_kg"] if row else None


def get_price_history(product_id: int) -> list[dict]:
    """سجل كل التعديلات اللي حصلت على سعر هذا الصنف، الأحدث أولاً."""
    rows = db.fetch_all(
        """SELECT dp.date, dp.price_per_kg, e.name as set_by_name
           FROM daily_prices dp
           LEFT JOIN employees e ON dp.set_by = e.id
           WHERE dp.product_id = ?
           ORDER BY dp.date DESC, dp.id DESC""",
        (product_id,),
    )
    return [dict(r) for r in rows]

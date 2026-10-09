"""
دوال تنسيق الأرقام
====================
مشتركة بين طبقة الخدمات (services) والواجهة (gui) - عشان كده هي في
utils/ المستقلة، مش جوه gui/، حتى الملفات اللي مالهاش علاقة بالواجهة
(زي services) تقدر تستخدمها من غير أي اعتماد دائري.

القاعدة: أي رقم صحيح (زي 1000 أو 25) يتعرض من غير فاصلة عشرية أو
أصفار زيادة (1000 مش 1000.00). الفاصلة العشرية تتعرض بس لما يكون
فيه كسر فعلي (25.5 تفضل 25.5، مش تتحول لـ 25 أو 25.50).
"""

from config import TON_DISPLAY_THRESHOLD_KG


def format_number(value, max_decimals: int = 2) -> str:
    """
    يعرض الرقم بدون كسور لو كان صحيح، وبأقل عدد كسور لازم لو فيه كسر فعلي.
    مثال: 1000.0 -> "1,000"   |   1000.5 -> "1,000.5"   |   1000.25 -> "1,000.25"
    """
    if value is None:
        return "-"

    rounded = round(float(value), max_decimals)

    if rounded == int(rounded):
        return f"{int(rounded):,}"

    text = f"{rounded:,.{max_decimals}f}"
    # نشيل أي أصفار زيادة في الآخر (وأي نقطة عشرية فاضية لو فضلت لوحدها)
    text = text.rstrip("0").rstrip(".")
    return text


def format_money(amount) -> str:
    return f"{format_number(amount)} ج.م"


def format_quantity(qty_kg) -> str:
    """يعرض الكمية بالطن لو كبيرة، وإلا بالكيلو - بدون كسور زيادة."""
    if qty_kg is None:
        return "-"
    if qty_kg >= TON_DISPLAY_THRESHOLD_KG:
        tons = qty_kg / 1000
        return f"{format_number(tons, 3)} طن ({format_number(qty_kg)} كجم)"
    return f"{format_number(qty_kg)} كجم"


def format_customer_code(customer_id) -> str:
    """كود مختصر ومميز لكل عميل (مبني على رقمه التسلسلي)، مثال: C0001."""
    if customer_id is None:
        return "-"
    return f"C{int(customer_id):04d}"

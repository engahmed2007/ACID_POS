"""
خدمة التقارير
===============
كل التقارير المطلوبة: مبيعات (فترة سريعة أو نطاق تاريخ مخصص)، أرباح،
أكتر نوع مبيعاً، أكتر عميل شراءً، وتقرير المديونيات (موجود في
customer_service).

ملحوظة عن الخصم: "الإجمالي" في تقرير المبيعات بيتحسب من المبلغ الفعلي
اللي دخل المحل بعد أي خصم (invoices.total_amount)، مش من مجموع بنود
الفواتير الخام، عشان الرقم يعبّر عن الفلوس الحقيقية اللي اتحصّلت.
"""

from datetime import date, timedelta

from database.db_manager import db


def _period_bounds(period: str) -> tuple[str, str]:
    """يحول 'daily'/'weekly'/'monthly' لتاريخ بداية ونهاية."""
    today = date.today()
    if period == "daily":
        start = today
    elif period == "weekly":
        start = today - timedelta(days=7)
    elif period == "monthly":
        start = today - timedelta(days=30)
    else:
        raise ValueError("period يجب أن يكون daily أو weekly أو monthly")
    return start.isoformat(), today.isoformat()


def sales_report(period: str = None, date_from: str = None, date_to: str = None) -> dict:
    """
    إجمالي الكمية والقيمة المباعة خلال الفترة المطلوبة.
    - لو مررت period ('daily'/'weekly'/'monthly') بيحسب الفترة تلقائياً.
    - أو ممرر date_from/date_to مباشرة لنطاق مخصص (مثلاً من التقويم).
    """
    if period:
        date_from, date_to = _period_bounds(period)
    elif not date_from or not date_to:
        raise ValueError("لازم تحدد period أو date_from و date_to")

    qty_row = db.fetch_one(
        """SELECT COALESCE(SUM(ii.quantity_kg), 0) as total_qty
           FROM invoice_items ii
           JOIN invoices i ON ii.invoice_id = i.id
           WHERE i.is_deleted = 0
             AND date(i.date_time) BETWEEN date(?) AND date(?)""",
        (date_from, date_to),
    )
    value_row = db.fetch_one(
        """SELECT COALESCE(SUM(total_amount), 0) as total_value,
                  COALESCE(SUM(discount_amount), 0) as total_discount,
                  COUNT(*) as invoice_count
           FROM invoices
           WHERE is_deleted = 0
             AND date(date_time) BETWEEN date(?) AND date(?)""",
        (date_from, date_to),
    )
    return {
        "period": period,
        "date_from": date_from,
        "date_to": date_to,
        "total_quantity_kg": qty_row["total_qty"],
        "total_value": value_row["total_value"],
        "total_discount": value_row["total_discount"],
        "invoice_count": value_row["invoice_count"],
    }


def profit_report(date_from: str = None, date_to: str = None) -> dict:
    """
    الفرق بين سعر الشراء وسعر البيع لكل عملية بيع، مجمّع لفترة معينة.
    لو مفيش تاريخ محدد بيدي تقرير كل الفترة.
    بيرجع الأرباح الإجمالية (قبل الخصم) والصافية (بعد خصم قيمة الخصومات
    الممنوحة في نفس الفترة).
    """
    query = """
        SELECT ii.quantity_kg, ii.price_per_kg_at_sale, ii.purchase_price_per_kg,
               p.name as product_name, i.date_time
        FROM invoice_items ii
        JOIN invoices i ON ii.invoice_id = i.id
        JOIN products p ON ii.product_id = p.id
        WHERE i.is_deleted = 0
    """
    params = []
    if date_from:
        query += " AND date(i.date_time) >= date(?)"
        params.append(date_from)
    if date_to:
        query += " AND date(i.date_time) <= date(?)"
        params.append(date_to)

    rows = db.fetch_all(query, tuple(params))
    total_profit = 0.0
    total_revenue = 0.0
    details = []
    for r in rows:
        purchase_price = r["purchase_price_per_kg"] or 0
        line_profit = (r["price_per_kg_at_sale"] - purchase_price) * r["quantity_kg"]
        total_profit += line_profit
        total_revenue += r["price_per_kg_at_sale"] * r["quantity_kg"]
        details.append(
            {
                "product_name": r["product_name"],
                "date_time": r["date_time"],
                "quantity_kg": r["quantity_kg"],
                "sale_price": r["price_per_kg_at_sale"],
                "purchase_price": purchase_price,
                "profit": round(line_profit, 2),
            }
        )

    discount_query = "SELECT COALESCE(SUM(discount_amount), 0) as total_discount FROM invoices WHERE is_deleted = 0"
    discount_params = []
    if date_from:
        discount_query += " AND date(date_time) >= date(?)"
        discount_params.append(date_from)
    if date_to:
        discount_query += " AND date(date_time) <= date(?)"
        discount_params.append(date_to)
    discount_row = db.fetch_one(discount_query, tuple(discount_params))
    total_discount = discount_row["total_discount"]

    return {
        "total_revenue": round(total_revenue, 2),
        "total_profit": round(total_profit, 2),
        "total_discount": round(total_discount, 2),
        "net_revenue": round(total_revenue - total_discount, 2),
        "net_profit": round(total_profit - total_discount, 2),
        "details": details,
    }


def top_products_report(date_from: str = None, date_to: str = None, limit: int = 10) -> list[dict]:
    query = """
        SELECT p.name as product_name,
               SUM(ii.quantity_kg) as total_qty,
               SUM(ii.line_total) as total_value
        FROM invoice_items ii
        JOIN invoices i ON ii.invoice_id = i.id
        JOIN products p ON ii.product_id = p.id
        WHERE i.is_deleted = 0
    """
    params = []
    if date_from:
        query += " AND date(i.date_time) >= date(?)"
        params.append(date_from)
    if date_to:
        query += " AND date(i.date_time) <= date(?)"
        params.append(date_to)
    query += " GROUP BY p.id ORDER BY total_qty DESC LIMIT ?"
    params.append(limit)

    rows = db.fetch_all(query, tuple(params))
    return [dict(r) for r in rows]


def top_customers_report(date_from: str = None, date_to: str = None, limit: int = 10) -> list[dict]:
    query = """
        SELECT c.name as customer_name,
               SUM(i.total_amount) as total_value,
               COUNT(i.id) as invoice_count
        FROM invoices i
        JOIN customers c ON i.customer_id = c.id
        WHERE i.is_deleted = 0
    """
    params = []
    if date_from:
        query += " AND date(i.date_time) >= date(?)"
        params.append(date_from)
    if date_to:
        query += " AND date(i.date_time) <= date(?)"
        params.append(date_to)
    query += " GROUP BY c.id ORDER BY total_value DESC LIMIT ?"
    params.append(limit)

    rows = db.fetch_all(query, tuple(params))
    return [dict(r) for r in rows]

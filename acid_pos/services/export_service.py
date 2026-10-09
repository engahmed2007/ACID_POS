"""
خدمة تصدير التقارير
======================
تصدير أي تقرير (قائمة من dict) لملف CSV بيتفتح مباشرة في Excel.
(اخترنا CSV لأنه مدمج في بايثون بدون أي مكتبات خارجية، ويشتغل فوراً
بدون تنصيب أي حاجة إضافية. لو احتجت ملف .xlsx بتنسيق وألوان، أو ملف
PDF جاهز للطباعة، ممكن نضيف مكتبة openpyxl أو reportlab بسهولة لاحقاً
لأن دالة التصدير معزولة هنا في مكان واحد.)
"""

import csv
import os
from datetime import datetime

from config import EXPORTS_DIR


def export_to_csv(rows: list[dict], report_name: str) -> str:
    if not rows:
        raise ValueError("لا توجد بيانات لتصديرها")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{report_name}_{timestamp}.csv"
    filepath = os.path.join(EXPORTS_DIR, filename)

    fieldnames = list(rows[0].keys())
    # نستخدم utf-8-sig عشان الحروف العربية تظهر صح لما يتفتح في Excel
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return filepath

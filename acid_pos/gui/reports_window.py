"""
شاشة التقارير
================
تبويبات منفصلة: مبيعات، أرباح، أكتر نوع/عميل، البحث عن الفواتير.
اختيار التواريخ بشكل تقويم (Calendar) بدل الكتابة اليدوية، مع إمكانية
تصدير أي تقرير كملف CSV (يفتح مباشرة في Excel).

كل صفوف التحكم (فلاتر البحث، أزرار العرض) بتتمركز في نص الشاشة بدل ما
تكون ملزوقة في الحافة اليمنى، عشان لما تفتح التقويم يبقى قدامه مساحة
فاضية كفاية يتعرض فيها من غير ما يتقطع عند حافة الشاشة. وزرار التنفيذ
(بحث/عرض) دايماً في نفس صف حقول التاريخ مباشرة، مش في صف منفصل تحته،
عشان التقويم ميغطيهوش وهو مفتوح.
"""

from datetime import date, timedelta

import tkinter as tk
from tkinter import ttk

from auth.auth_manager import auth_manager
from services import reports_service, sales_service, export_service
from gui.widgets.common import (
    FONT_TITLE, FONT_BOLD, FONT_NORMAL, COLOR_PRIMARY, COLOR_DANGER, COLOR_SUCCESS,
    make_treeview, clear_treeview, show_error, show_info, confirm,
    labeled_entry, date_picker, format_money, format_number,
)
from utils.ui_helpers import set_window_icon, maximize_window


def _field_group(parent, builder):
    """
    يبني مجموعة عنصر واحد (label + widget) جوه إطار صغير مستقل، عشان
    نقدر نرصّهم جنب بعض بـ pack بدل ما نحسب أرقام أعمدة grid يدوياً.
    """
    frame = ttk.Frame(parent)
    widget = builder(frame)
    return frame, widget


def _centered_row(parent, pady=8):
    """
    صف تحكم يتمركز في نص الشاشة (مش ملزوق في الحافة اليمنى) - ده اللي
    بيسيب مساحة فاضية على الجنبين عشان أي قائمة منسدلة أو تقويم يتعرض
    كامل من غير ما يتقطع عند حافة النافذة.
    """
    row = ttk.Frame(parent)
    row.pack(pady=pady)
    return row


class ReportsWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("التقارير")
        set_window_icon(self)
        maximize_window(self)

        tk.Label(self, text="التقارير", font=FONT_TITLE, fg=COLOR_PRIMARY).pack(pady=8)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.sales_tab = SalesReportTab(notebook)
        self.profit_tab = ProfitReportTab(notebook)
        self.top_tab = TopReportsTab(notebook)
        self.search_tab = InvoiceSearchTab(notebook)

        notebook.add(self.sales_tab, text="تقرير المبيعات")
        notebook.add(self.profit_tab, text="تقرير الأرباح")
        notebook.add(self.top_tab, text="الأكثر مبيعاً")
        notebook.add(self.search_tab, text="البحث عن فاتورة")


class SalesReportTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        # --- فترات سريعة جاهزة ---
        quick_frame = ttk.LabelFrame(self, text="فترة سريعة")
        quick_frame.pack(fill="x", padx=10, pady=8)

        row = _centered_row(quick_frame)
        self.period_var = tk.StringVar(value="daily")
        for value, label in [("monthly", "آخر شهر"), ("weekly", "آخر أسبوع"), ("daily", "اليوم")]:
            ttk.Radiobutton(row, text=label, value=value, variable=self.period_var).pack(side="right", padx=10)

        tk.Button(
            row, text="📊 عرض التقرير", font=FONT_BOLD, bg="#e8f0fe", command=self._show_quick_report,
        ).pack(side="right", padx=(30, 10))

        # --- نطاق مخصص من التقويم ---
        custom_frame = ttk.LabelFrame(self, text="أو نطاق تاريخ مخصص من التقويم")
        custom_frame.pack(fill="x", padx=10, pady=8)

        row2 = _centered_row(custom_frame)
        today = date.today()
        from_frame, self.from_picker = _field_group(
            row2, lambda p: date_picker(p, "من تاريخ:", 0, col=0, initial_date=today - timedelta(days=7))[1]
        )
        from_frame.pack(side="right", padx=10)

        to_frame, self.to_picker = _field_group(
            row2, lambda p: date_picker(p, "إلى تاريخ:", 0, col=0, initial_date=today)[1]
        )
        to_frame.pack(side="right", padx=10)

        tk.Button(
            row2, text="📅 عرض النطاق", font=FONT_BOLD, bg="#e8f0fe", command=self._show_custom_report,
        ).pack(side="right", padx=(30, 10))

        self.result_label = tk.Label(self, text="", font=FONT_BOLD, justify="right")
        self.result_label.pack(pady=20)

    def _display(self, report):
        text = (
            f"الفترة من {report['date_from']} إلى {report['date_to']}\n\n"
            f"عدد الفواتير: {report['invoice_count']}\n"
            f"إجمالي الكمية المباعة: {format_number(report['total_quantity_kg'])} كجم\n"
            f"إجمالي الخصومات: {format_money(report['total_discount'])}\n"
            f"إجمالي قيمة المبيعات (بعد الخصم): {format_money(report['total_value'])}"
        )
        self.result_label.config(text=text)

    def _show_quick_report(self):
        report = reports_service.sales_report(period=self.period_var.get())
        self._display(report)

    def _show_custom_report(self):
        date_from = self.from_picker.get_date().isoformat()
        date_to = self.to_picker.get_date().isoformat()
        if date_from > date_to:
            show_error("تاريخ البداية لازم يكون قبل تاريخ النهاية")
            return
        report = reports_service.sales_report(date_from=date_from, date_to=date_to)
        self._display(report)


class ProfitReportTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        control = ttk.LabelFrame(self, text="فترة التقرير")
        control.pack(fill="x", padx=10, pady=8)

        row = _centered_row(control)
        today = date.today()
        from_frame, self.from_picker = _field_group(
            row, lambda p: date_picker(p, "من تاريخ:", 0, col=0, initial_date=today - timedelta(days=30))[1]
        )
        from_frame.pack(side="right", padx=10)

        to_frame, self.to_picker = _field_group(
            row, lambda p: date_picker(p, "إلى تاريخ:", 0, col=0, initial_date=today)[1]
        )
        to_frame.pack(side="right", padx=10)

        tk.Button(
            row, text="📊 عرض", font=FONT_BOLD, bg="#e8f0fe", command=self._show_report,
        ).pack(side="right", padx=(30, 10))

        self.all_time_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            control, text="كل الفترة (تجاهل التاريخ)", variable=self.all_time_var
        ).pack(pady=(0, 10))

        self.summary_label = tk.Label(self, text="", font=FONT_BOLD, justify="right")
        self.summary_label.pack(pady=10)

        self.tree = make_treeview(
            self,
            {
                "product": ("الصنف", 160), "date": ("التاريخ", 140), "qty": ("الكمية", 100),
                "sale_price": ("سعر البيع", 100), "purchase_price": ("سعر الشراء", 100),
                "profit": ("الربح", 100),
            },
        )

    def _show_report(self):
        if self.all_time_var.get():
            date_from, date_to = None, None
        else:
            date_from = self.from_picker.get_date().isoformat()
            date_to = self.to_picker.get_date().isoformat()
            if date_from > date_to:
                show_error("تاريخ البداية لازم يكون قبل تاريخ النهاية")
                return

        report = reports_service.profit_report(date_from, date_to)
        self.summary_label.config(
            text=f"إجمالي المبيعات: {format_money(report['total_revenue'])}   |   "
                 f"إجمالي الأرباح: {format_money(report['total_profit'])}   |   "
                 f"إجمالي الخصومات: {format_money(report['total_discount'])}   |   "
                 f"صافي الربح بعد الخصم: {format_money(report['net_profit'])}"
        )
        clear_treeview(self.tree)
        for row in report["details"]:
            self.tree.insert(
                "", "end",
                values=(
                    row["product_name"], row["date_time"], format_number(row["quantity_kg"]),
                    format_number(row["sale_price"]), format_number(row["purchase_price"]),
                    format_money(row["profit"]),
                ),
            )


class TopReportsTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        control = ttk.LabelFrame(self, text="اختر التقرير")
        control.pack(fill="x", padx=10, pady=8)

        row = _centered_row(control)
        tk.Button(row, text="📦 أكثر نوع مبيعاً", font=FONT_BOLD, bg="#e8f0fe",
                  command=self._show_top_products).pack(side="right", padx=10)
        tk.Button(row, text="👤 أكثر عميل شراءً", font=FONT_BOLD, bg="#e8f0fe",
                  command=self._show_top_customers).pack(side="right", padx=10)

        self.tree = make_treeview(self, {"name": ("الاسم", 250), "value": ("القيمة الإجمالية", 200), "extra": ("تفاصيل", 200)})

    def _show_top_products(self):
        clear_treeview(self.tree)
        self.tree.heading("name", text="الصنف")
        self.tree.heading("extra", text="الكمية (كجم)")
        for row in reports_service.top_products_report():
            self.tree.insert(
                "", "end",
                values=(row["product_name"], format_money(row["total_value"]), format_number(row["total_qty"])),
            )

    def _show_top_customers(self):
        clear_treeview(self.tree)
        self.tree.heading("name", text="العميل")
        self.tree.heading("extra", text="عدد الفواتير")
        for row in reports_service.top_customers_report():
            self.tree.insert(
                "", "end",
                values=(row["customer_name"], format_money(row["total_value"]), row["invoice_count"]),
            )


class InvoiceSearchTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        control = ttk.LabelFrame(self, text="فلاتر البحث")
        control.pack(fill="x", padx=10, pady=8)

        # --- الصف الأول: رقم الفاتورة + اسم العميل ---
        row1 = _centered_row(control, pady=(10, 4))

        id_frame, self.id_entry = _field_group(
            row1, lambda p: labeled_entry(p, "رقم الفاتورة:", 0, col=0, width=10)[1]
        )
        id_frame.pack(side="right", padx=10)

        customer_frame, self.customer_entry = _field_group(
            row1, lambda p: labeled_entry(p, "اسم العميل:", 0, col=0)[1]
        )
        customer_frame.pack(side="right", padx=10)

        # --- الصف الثاني: نطاق التاريخ + زر البحث في نفس الصف
        # (عشان زر البحث يفضل ظاهر جنب الحقول ومش تحت التقويم لما يتفتح) ---
        row2 = _centered_row(control, pady=4)

        today = date.today()
        from_frame, self.from_picker = _field_group(
            row2, lambda p: date_picker(p, "من تاريخ:", 0, col=0, initial_date=today - timedelta(days=30))[1]
        )
        from_frame.pack(side="right", padx=10)

        to_frame, self.to_picker = _field_group(
            row2, lambda p: date_picker(p, "إلى تاريخ:", 0, col=0, initial_date=today)[1]
        )
        to_frame.pack(side="right", padx=10)

        tk.Button(
            row2, text="🔍 بحث", font=FONT_BOLD, bg=COLOR_SUCCESS, fg="white", command=self._search,
        ).pack(side="right", padx=(30, 10))

        # --- الصف الثالث: خيار تجاهل التاريخ لوحده ---
        row3 = _centered_row(control, pady=(4, 10))
        self.all_dates_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            row3, text="كل التواريخ (تجاهل الفلتر الزمني)", variable=self.all_dates_var
        ).pack()

        self.tree = make_treeview(
            self,
            {
                "id": ("رقم", 60), "date": ("التاريخ", 150), "customer": ("العميل", 160),
                "total": ("الإجمالي", 120), "credit": ("آجل؟", 80),
            },
        )

        action_frame = ttk.Frame(self)
        action_frame.pack(fill="x", pady=5)
        tk.Button(action_frame, text="🗑 حذف الفاتورة المحددة", font=FONT_NORMAL,
                  command=self._delete_selected).pack(side="right", padx=8)
        tk.Button(action_frame, text="⬇ تصدير النتائج CSV", font=FONT_NORMAL,
                  command=self._export).pack(side="right", padx=8)

        self._last_results = []
        self._search()

    def _search(self):
        invoice_id = self.id_entry.get().strip()

        if self.all_dates_var.get():
            date_from, date_to = None, None
        else:
            date_from = self.from_picker.get_date().isoformat()
            date_to = self.to_picker.get_date().isoformat()
            if date_from > date_to:
                show_error("تاريخ البداية لازم يكون قبل تاريخ النهاية")
                return

        results = sales_service.search_invoices(
            date_from=date_from,
            date_to=date_to,
            customer_name=self.customer_entry.get().strip() or None,
            invoice_id=int(invoice_id) if invoice_id.isdigit() else None,
        )
        self._last_results = results
        clear_treeview(self.tree)
        for r in results:
            self.tree.insert(
                "", "end",
                values=(
                    r["id"], r["date_time"], r["customer_name"] or "-",
                    format_money(r["total_amount"]),
                    "نعم" if r["is_credit"] else "لا",
                ),
            )

    def _delete_selected(self):
        if not auth_manager.has_permission("invoices_delete"):
            show_error("ليس لديك صلاحية حذف الفواتير - تواصل مع المدير")
            return
        selected = self.tree.selection()
        if not selected:
            show_error("اختر فاتورة أولاً")
            return
        values = self.tree.item(selected[0], "values")
        invoice_id = int(values[0])
        if not confirm(f"هل أنت متأكد من حذف الفاتورة رقم {invoice_id}؟ سيتم إرجاع الكمية للمخزون."):
            return
        try:
            sales_service.delete_invoice(invoice_id, auth_manager.current_employee.id)
        except ValueError as e:
            show_error(str(e))
            return
        show_info("تم حذف الفاتورة بنجاح")
        self._search()

    def _export(self):
        if not self._last_results:
            show_error("لا توجد نتائج لتصديرها، ابحث أولاً")
            return
        try:
            path = export_service.export_to_csv(self._last_results, "invoices_search")
            show_info(f"تم التصدير بنجاح:\n{path}")
        except Exception as e:
            show_error(str(e))

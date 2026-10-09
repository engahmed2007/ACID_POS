"""
شاشة حسابات العملاء (آجل / ديون)
===================================
تبويبان داخل نفس الشاشة: "كل العملاء" و"تقرير المديونيات" - بدون فتح
أي نافذة جديدة عند عرض التقرير، حفاظاً على مبدأ شاشة واحدة لكل أيقونة.
كل عميل له كود مميز (مثال: C0001) بيظهر جنب اسمه في كل مكان.
"""

import tkinter as tk
from tkinter import ttk

from auth.auth_manager import auth_manager
from services import customer_service
from gui.widgets.common import (
    FONT_TITLE, FONT_BOLD, FONT_NORMAL, COLOR_PRIMARY, COLOR_DANGER,
    make_treeview, clear_treeview, show_error, show_info, labeled_entry, format_money,
)
from utils.ui_helpers import set_window_icon, maximize_window


class CustomersWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("حسابات العملاء")
        set_window_icon(self)
        maximize_window(self)

        tk.Label(self, text="حسابات العملاء (آجل / ديون)", font=FONT_TITLE, fg=COLOR_PRIMARY).pack(pady=10)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.customers_tab = CustomersListTab(notebook, on_change=self._refresh_debtors_tab)
        self.debtors_tab = DebtorsReportTab(notebook)

        notebook.add(self.customers_tab, text="كل العملاء")
        notebook.add(self.debtors_tab, text="تقرير المديونيات")

        notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _on_tab_changed(self, event):
        self.debtors_tab.refresh()

    def _refresh_debtors_tab(self):
        self.debtors_tab.refresh()


class CustomersListTab(ttk.Frame):
    def __init__(self, parent, on_change=None):
        super().__init__(parent)
        self.on_change = on_change
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        # --- بحث بالاسم أو الكود ---
        search_frame = ttk.Frame(self)
        search_frame.pack(fill="x", padx=15, pady=(10, 0))
        _, self.search_entry = labeled_entry(search_frame, "بحث بالاسم أو الكود:", 0, col=1)
        self.search_entry.bind("<KeyRelease>", lambda e: self._refresh())
        tk.Button(search_frame, text="مسح البحث", font=FONT_NORMAL, command=self._clear_search).grid(
            row=0, column=2, padx=10
        )

        table_frame = ttk.Frame(self)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.tree = make_treeview(
            table_frame,
            {
                "code": ("الكود", 90),
                "name": ("اسم العميل", 200),
                "phone": ("رقم الهاتف", 150),
                "debt": ("إجمالي المديونية", 170),
            },
        )

        # --- إضافة عميل جديد ---
        add_frame = ttk.LabelFrame(self, text="إضافة عميل جديد")
        add_frame.pack(fill="x", padx=15, pady=8)
        _, self.new_name_entry = labeled_entry(add_frame, "الاسم:", 0, col=2)
        _, self.new_phone_entry = labeled_entry(add_frame, "رقم الهاتف:", 0, col=0)
        tk.Button(add_frame, text="➕ إضافة", font=FONT_NORMAL, command=self._add_customer).grid(
            row=0, column=4, padx=10
        )

        # --- تسجيل دفعة ---
        payment_frame = ttk.LabelFrame(self, text="تسجيل دفعة على حساب عميل")
        payment_frame.pack(fill="x", padx=15, pady=8)

        ttk.Label(payment_frame, text="العميل:", font=FONT_NORMAL).grid(row=0, column=3, padx=5, pady=5)
        self.customer_combo = ttk.Combobox(payment_frame, font=FONT_NORMAL, width=28, state="readonly")
        self.customer_combo.grid(row=0, column=2, padx=5)

        _, self.payment_amount_entry = labeled_entry(payment_frame, "قيمة الدفعة:", 0, col=0)

        tk.Button(
            payment_frame, text="💵 تسجيل الدفعة", font=FONT_BOLD, command=self._record_payment
        ).grid(row=0, column=4, padx=10)

    def _clear_search(self):
        self.search_entry.delete(0, tk.END)
        self._refresh()

    def _refresh(self):
        clear_treeview(self.tree)
        query = self.search_entry.get().strip() if hasattr(self, "search_entry") else ""
        customers = customer_service.search_customers(query)
        for c in customers:
            self.tree.insert("", "end", values=(c.code or "-", c.name, c.phone or "-", format_money(c.total_debt)))

        # قائمة الدفعات دايماً بتعرض كل العملاء (مش متأثرة بمربع البحث)
        all_customers = customer_service.list_customers()
        combo_values = [f"{c.name} ({c.code})" for c in all_customers]
        self.customer_combo.config(values=combo_values)
        self._customers_by_combo_label = {f"{c.name} ({c.code})": c for c in all_customers}

    def _add_customer(self):
        name = self.new_name_entry.get().strip()
        if not name:
            show_error("أدخل اسم العميل")
            return
        phone = self.new_phone_entry.get().strip() or None
        customer_service.add_customer(name, phone)
        self.new_name_entry.delete(0, tk.END)
        self.new_phone_entry.delete(0, tk.END)
        self._refresh()
        if self.on_change:
            self.on_change()

    def _record_payment(self):
        label = self.customer_combo.get()
        customer = self._customers_by_combo_label.get(label)
        if not customer:
            show_error("اختر العميل أولاً")
            return
        try:
            amount = float(self.payment_amount_entry.get())
        except ValueError:
            show_error("أدخل قيمة صحيحة")
            return
        try:
            customer_service.record_payment(
                customer.id, amount, auth_manager.current_employee.id
            )
        except ValueError as e:
            show_error(str(e))
            return
        show_info(f"تم تسجيل دفعة بقيمة {format_money(amount)} من {customer.name}")
        self.payment_amount_entry.delete(0, tk.END)
        self._refresh()
        if self.on_change:
            self.on_change()


class DebtorsReportTab(ttk.Frame):
    """تقرير العملاء المدينين، مرتب من الأكبر مديونية للأصغر - مدمج داخل نفس الشاشة."""

    def __init__(self, parent):
        super().__init__(parent)
        tk.Label(
            self, text="العملاء المدينون (من الأكبر للأصغر)", font=FONT_BOLD, fg=COLOR_DANGER,
        ).pack(pady=10)

        tk.Button(self, text="🔄 تحديث", font=FONT_NORMAL, command=self.refresh).pack(pady=5)

        self.tree = make_treeview(
            self,
            {"code": ("الكود", 90), "name": ("اسم العميل", 200), "phone": ("الهاتف", 140), "debt": ("المديونية", 150)},
        )
        self.refresh()

    def refresh(self):
        clear_treeview(self.tree)
        for row in customer_service.get_debtors_report():
            self.tree.insert(
                "", "end",
                values=(row["code"] or "-", row["name"], row["phone"] or "-", format_money(row["total_debt"])),
            )

"""
شاشة البيع والفواتير
=======================
اختيار الصنف، إدخال الكمية، السعر بيتحسب تلقائي من السعر الثابت المسجل
(مع إمكانية تعديله يدوي لفاتورة معينة بس)، إضافة أكتر من صنف، وخصم
اختياري على الفاتورة. بيانات العميل (بحث/اختيار) بتظهر بس لو الفاتورة
آجلة - البيع النقدي المباشر مايتسجلش عليه أي اسم عميل خالص.
"""

import tkinter as tk
from tkinter import ttk

from auth.auth_manager import auth_manager
from services import inventory_service, pricing_service, sales_service, customer_service
from services.sales_service import SaleItemInput
from gui.widgets.common import (
    FONT_TITLE, FONT_BOLD, FONT_NORMAL, COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER,
    make_treeview, clear_treeview, show_error, show_info, format_money, format_number,
)
from utils.ui_helpers import set_window_icon, maximize_window


class NewCustomerDialog(tk.Toplevel):
    """نافذة صغيرة لإضافة عميل جديد بسرعة من داخل شاشة البيع نفسها."""

    def __init__(self, parent, on_created):
        super().__init__(parent)
        self.on_created = on_created
        self.title("إضافة عميل جديد")
        self.geometry("360x220")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        container = ttk.Frame(self)
        container.pack(expand=True, pady=20)

        tk.Label(container, text="إضافة عميل جديد", font=FONT_BOLD, fg=COLOR_PRIMARY).grid(
            row=0, column=0, columnspan=2, pady=(0, 15)
        )

        ttk.Label(container, text="الاسم:", font=FONT_NORMAL).grid(row=1, column=1, sticky="e", padx=5, pady=8)
        self.name_entry = ttk.Entry(container, font=FONT_NORMAL, width=22)
        self.name_entry.grid(row=1, column=0, padx=5, pady=8)

        ttk.Label(container, text="رقم الهاتف:", font=FONT_NORMAL).grid(row=2, column=1, sticky="e", padx=5, pady=8)
        self.phone_entry = ttk.Entry(container, font=FONT_NORMAL, width=22)
        self.phone_entry.grid(row=2, column=0, padx=5, pady=8)

        tk.Button(
            container, text="💾 حفظ وإضافة", font=FONT_BOLD, bg=COLOR_SUCCESS, fg="white",
            command=self._save,
        ).grid(row=3, column=0, columnspan=2, pady=15)

        self.name_entry.focus_set()

    def _save(self):
        name = self.name_entry.get().strip()
        if not name:
            show_error("أدخل اسم العميل")
            return
        phone = self.phone_entry.get().strip() or None
        customer_id = customer_service.add_customer(name, phone)
        customer = customer_service.get_customer(customer_id)
        self.on_created(customer)
        self.destroy()


class SalesWindow(tk.Toplevel):
    def __init__(self, parent, on_close_refresh=None):
        super().__init__(parent)
        self.on_close_refresh = on_close_refresh
        self.title("فاتورة بيع جديدة")
        set_window_icon(self)
        maximize_window(self)

        self.cart: list[SaleItemInput] = []
        self.products = inventory_service.list_products()
        self.product_by_name = {p.name: p for p in self.products}
        self.selected_customer = None
        self._customer_map = {}

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---------------------------------------------------------------
    def _build_ui(self):
        header_frame = ttk.Frame(self)
        header_frame.pack(fill="x")

        tk.Label(header_frame, text="فاتورة بيع جديدة", font=FONT_TITLE, fg=COLOR_PRIMARY).pack(
            side="right", padx=20, pady=10
        )
        self.invoice_number_label = tk.Label(
            header_frame, text="", font=FONT_BOLD, fg=COLOR_SUCCESS
        )
        self.invoice_number_label.pack(side="left", padx=20, pady=10)
        self._refresh_invoice_number()

        # --- نوع الفاتورة وبيانات العميل (للآجل فقط) ---
        customer_frame = ttk.LabelFrame(self, text="نوع الفاتورة")
        customer_frame.pack(fill="x", padx=15, pady=8)

        self.is_credit_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            customer_frame, text="فاتورة آجلة (على الحساب) - يتطلب اختيار عميل",
            variable=self.is_credit_var, command=self._on_credit_toggle,
        ).pack(anchor="e", padx=10, pady=(8, 4))

        # هذا الإطار يظهر بس لو الفاتورة آجلة - البيع النقدي المباشر
        # مايتسجلش عليه أي اسم عميل خالص
        self.credit_customer_frame = ttk.Frame(customer_frame)

        search_row = ttk.Frame(self.credit_customer_frame)
        search_row.pack(fill="x", pady=4, padx=10)
        ttk.Label(search_row, text="بحث بالاسم أو الكود:", font=FONT_NORMAL).pack(side="right", padx=5)
        self.customer_search_entry = ttk.Entry(search_row, font=FONT_NORMAL, width=22)
        self.customer_search_entry.pack(side="right", padx=5)
        self.customer_search_entry.bind("<KeyRelease>", lambda e: self._filter_customers())

        select_row = ttk.Frame(self.credit_customer_frame)
        select_row.pack(fill="x", pady=4, padx=10)
        ttk.Label(select_row, text="اختر العميل:", font=FONT_NORMAL).pack(side="right", padx=5)
        self.customer_select_combo = ttk.Combobox(select_row, font=FONT_NORMAL, width=30, state="readonly")
        self.customer_select_combo.pack(side="right", padx=5)
        self.customer_select_combo.bind("<<ComboboxSelected>>", self._on_customer_selected)

        tk.Button(
            select_row, text="➕ عميل جديد", font=FONT_NORMAL, command=self._open_new_customer_dialog
        ).pack(side="left", padx=5)

        self.selected_customer_label = tk.Label(
            self.credit_customer_frame, text="لم يتم اختيار عميل بعد",
            font=FONT_NORMAL, fg=COLOR_DANGER,
        )
        self.selected_customer_label.pack(anchor="e", padx=10, pady=(0, 8))

        # --- إضافة صنف ---
        item_frame = ttk.LabelFrame(self, text="إضافة صنف للفاتورة")
        item_frame.pack(fill="x", padx=15, pady=8)

        ttk.Label(item_frame, text="الصنف:", font=FONT_NORMAL).grid(row=0, column=3, padx=5, pady=8)
        self.product_combo = ttk.Combobox(
            item_frame, values=list(self.product_by_name.keys()), font=FONT_NORMAL,
            width=22, state="readonly",
        )
        self.product_combo.grid(row=0, column=2, padx=5)
        self.product_combo.bind("<<ComboboxSelected>>", self._on_product_selected)

        ttk.Label(item_frame, text="الكمية (كجم):", font=FONT_NORMAL).grid(row=0, column=1, padx=5)
        self.qty_entry = ttk.Entry(item_frame, font=FONT_NORMAL, width=10)
        self.qty_entry.grid(row=0, column=0, padx=5)

        ttk.Label(item_frame, text="سعر الكيلو:", font=FONT_NORMAL).grid(row=1, column=1, padx=5, pady=5)
        self.price_entry = ttk.Entry(item_frame, font=FONT_NORMAL, width=10)
        self.price_entry.grid(row=1, column=0, padx=5)

        self.stock_label = tk.Label(item_frame, text="", font=FONT_NORMAL, fg="#555")
        self.stock_label.grid(row=1, column=2, columnspan=2, sticky="w", padx=5)

        add_btn = tk.Button(
            item_frame, text="➕ إضافة للفاتورة", font=FONT_BOLD, bg="#e8f0fe",
            command=self._add_item_to_cart,
        )
        add_btn.grid(row=0, column=4, rowspan=2, padx=15)

        # --- الخصم (نثبته بالأسفل الأول عشان يفضل ظاهر دايماً) ---
        discount_frame = ttk.LabelFrame(self, text="خصم على الفاتورة (اختياري)")
        discount_frame.pack(side="bottom", fill="x", padx=15, pady=8)

        self.discount_type_var = tk.StringVar(value="fixed")
        ttk.Radiobutton(
            discount_frame, text="مبلغ ثابت (ج.م)", value="fixed",
            variable=self.discount_type_var, command=self._update_total,
        ).grid(row=0, column=3, padx=8)
        ttk.Radiobutton(
            discount_frame, text="نسبة مئوية (%)", value="percent",
            variable=self.discount_type_var, command=self._update_total,
        ).grid(row=0, column=2, padx=8)

        ttk.Label(discount_frame, text="قيمة الخصم:", font=FONT_NORMAL).grid(row=0, column=1, padx=5)
        self.discount_value_entry = ttk.Entry(discount_frame, font=FONT_NORMAL, width=10)
        self.discount_value_entry.grid(row=0, column=0, padx=5)
        self.discount_value_entry.insert(0, "0")
        self.discount_value_entry.bind("<KeyRelease>", lambda e: self._update_total())

        # --- الإجمالي والحفظ (مثبتة بالأسفل برضه، فوق إطار الخصم مباشرة) ---
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(side="bottom", fill="x", padx=15, pady=10)

        totals_frame = ttk.Frame(bottom_frame)
        totals_frame.pack(side="right", padx=10)

        self.subtotal_label = tk.Label(totals_frame, text="", font=FONT_NORMAL, fg="#555")
        self.subtotal_label.pack(anchor="e")

        self.discount_label = tk.Label(totals_frame, text="", font=FONT_NORMAL, fg="#c0392b")
        self.discount_label.pack(anchor="e")

        self.total_label = tk.Label(
            totals_frame, text=f"الإجمالي: {format_money(0)}", font=FONT_TITLE, fg=COLOR_SUCCESS
        )
        self.total_label.pack(anchor="e")

        save_btn = tk.Button(
            bottom_frame, text="✅ حفظ الفاتورة", font=FONT_BOLD, bg=COLOR_SUCCESS, fg="white",
            width=20, height=2, command=self._save_invoice,
        )
        save_btn.pack(side="left", padx=10)

        # --- عناصر الفاتورة (بتاخد آخر مساحة متبقية، وتتقلص هي اللي بتضغط
        # عشان الخصم والإجمالي وزرار الحفظ يفضلوا ظاهرين دايماً فوق أي شاشة) ---
        cart_frame = ttk.LabelFrame(self, text="أصناف الفاتورة")
        cart_frame.pack(side="top", fill="both", expand=True, padx=15, pady=8)

        self.cart_tree = make_treeview(
            cart_frame,
            {
                "product": ("الصنف", 200),
                "qty": ("الكمية (كجم)", 120),
                "price": ("سعر الكيلو", 120),
                "total": ("الإجمالي", 120),
            },
            height=6,
        )

        remove_btn = tk.Button(
            cart_frame, text="🗑 حذف الصنف المحدد", font=FONT_NORMAL,
            command=self._remove_selected_item,
        )
        remove_btn.pack(pady=5)

        self._update_total()

    # ---------------------------------------------------------------
    def _on_credit_toggle(self):
        if self.is_credit_var.get():
            self.credit_customer_frame.pack(fill="x")
            self._filter_customers()
        else:
            self.credit_customer_frame.pack_forget()
            self.selected_customer = None
            self.customer_search_entry.delete(0, tk.END)
            self.customer_select_combo.set("")
            self.selected_customer_label.config(text="لم يتم اختيار عميل بعد", fg=COLOR_DANGER)

    def _filter_customers(self):
        query = self.customer_search_entry.get().strip()
        results = customer_service.search_customers(query)
        labels = [f"{c.name} ({c.code})" for c in results]
        self.customer_select_combo.config(values=labels)
        self._customer_map = {f"{c.name} ({c.code})": c for c in results}

    def _on_customer_selected(self, event=None):
        label = self.customer_select_combo.get()
        customer = self._customer_map.get(label)
        if customer:
            self.selected_customer = customer
            self.selected_customer_label.config(
                text=f"العميل المحدد: {customer.name} ({customer.code})", fg=COLOR_SUCCESS
            )

    def _open_new_customer_dialog(self):
        def on_created(customer):
            self.selected_customer = customer
            self.selected_customer_label.config(
                text=f"العميل المحدد: {customer.name} ({customer.code})", fg=COLOR_SUCCESS
            )
            self._filter_customers()
            self.customer_select_combo.set(f"{customer.name} ({customer.code})")

        NewCustomerDialog(self, on_created)

    # ---------------------------------------------------------------
    def _refresh_invoice_number(self):
        next_number = sales_service.get_next_invoice_number()
        self.invoice_number_label.config(text=f"رقم الفاتورة: {next_number}")

    def _on_product_selected(self, event=None):
        name = self.product_combo.get()
        product = self.product_by_name.get(name)
        if not product:
            return
        current_price = pricing_service.get_current_price(product.id)
        if current_price is not None:
            self.price_entry.delete(0, tk.END)
            self.price_entry.insert(0, format_number(current_price))
        self.stock_label.config(
            text=f"المتاح بالمخزون: {inventory_service.format_quantity(product.current_quantity_kg)}"
        )

    def _add_item_to_cart(self):
        name = self.product_combo.get()
        product = self.product_by_name.get(name)
        if not product:
            show_error("اختر الصنف أولاً")
            return
        try:
            qty = float(self.qty_entry.get())
            price = float(self.price_entry.get())
        except ValueError:
            show_error("الكمية والسعر يجب أن يكونا أرقام صحيحة")
            return

        if qty <= 0 or price <= 0:
            show_error("الكمية والسعر يجب أن يكونا أكبر من صفر")
            return

        if qty > product.current_quantity_kg:
            show_error(
                f"الكمية المطلوبة أكبر من المتاح بالمخزون "
                f"({inventory_service.format_quantity(product.current_quantity_kg)})"
            )
            return

        item = SaleItemInput(product.id, qty, price)
        self.cart.append(item)
        self.cart_tree.insert(
            "", "end",
            values=(product.name, format_number(qty), format_number(price), format_money(item.line_total)),
        )
        self.qty_entry.delete(0, tk.END)
        self._update_total()

    def _remove_selected_item(self):
        selected = self.cart_tree.selection()
        if not selected:
            return
        for sel in selected:
            index = self.cart_tree.index(sel)
            self.cart_tree.delete(sel)
            del self.cart[index]
        self._update_total()

    def _compute_discount_amount(self, subtotal: float) -> float:
        """
        يحسب قيمة الخصم بالجنيه من قيمة مربع الخصم اللي دخلها المستخدم،
        حسب الصنف المختار (مبلغ ثابت أو نسبة مئوية). بيرجع صفر لو القيمة
        غير صحيحة أو فاضية، عشان العرض التلقائي متعملش أخطاء وهو لسه بيكتب.
        """
        try:
            raw_value = float(self.discount_value_entry.get())
        except ValueError:
            return 0.0
        if raw_value <= 0:
            return 0.0

        if self.discount_type_var.get() == "percent":
            raw_value = min(raw_value, 100)
            discount = subtotal * raw_value / 100
        else:
            discount = raw_value

        return min(discount, subtotal)

    def _update_total(self):
        subtotal = sum(i.line_total for i in self.cart)
        discount = self._compute_discount_amount(subtotal)
        total = subtotal - discount

        self.subtotal_label.config(text=f"الإجمالي قبل الخصم: {format_money(subtotal)}")
        self.discount_label.config(text=f"الخصم: {format_money(discount)}")
        self.total_label.config(text=f"الإجمالي النهائي: {format_money(total)}")

    # ---------------------------------------------------------------
    def _save_invoice(self):
        if not self.cart:
            show_error("أضف صنف واحد على الأقل قبل الحفظ")
            return

        is_credit = self.is_credit_var.get()
        customer_id = None

        if is_credit:
            if self.selected_customer is None:
                show_error("اختر عميل (أو أضف عميل جديد) عشان تسجل فاتورة آجلة")
                return
            customer_id = self.selected_customer.id

        subtotal = sum(i.line_total for i in self.cart)
        discount_amount = self._compute_discount_amount(subtotal)

        try:
            invoice_id = sales_service.create_invoice(
                employee_id=auth_manager.current_employee.id,
                items=self.cart,
                customer_id=customer_id,
                is_credit=is_credit,
                discount_amount=discount_amount,
            )
        except ValueError as e:
            show_error(str(e))
            return

        show_info(f"تم حفظ الفاتورة رقم {invoice_id} بنجاح.")
        self._reset_form()

    def _reset_form(self):
        self.cart = []
        clear_treeview(self.cart_tree)
        self.discount_value_entry.delete(0, tk.END)
        self.discount_value_entry.insert(0, "0")
        self.discount_type_var.set("fixed")
        self._update_total()
        self.is_credit_var.set(False)
        self._on_credit_toggle()
        self.products = inventory_service.list_products()
        self.product_by_name = {p.name: p for p in self.products}
        self.product_combo.config(values=list(self.product_by_name.keys()))
        self._refresh_invoice_number()

    def _on_close(self):
        if self.on_close_refresh:
            self.on_close_refresh()
        self.destroy()

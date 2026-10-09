"""
شاشة إدارة المخزون + شاشة السعر الثابت للبيع
=================================================
"""

import tkinter as tk
from tkinter import ttk

from auth.auth_manager import auth_manager
from services import inventory_service, pricing_service
from gui.widgets.common import (
    FONT_TITLE, FONT_BOLD, FONT_NORMAL, COLOR_PRIMARY,
    make_treeview, clear_treeview, show_error, show_info, confirm, labeled_entry, format_number,
)
from utils.ui_helpers import set_window_icon, maximize_window


class InventoryWindow(tk.Toplevel):
    def __init__(self, parent, on_close_refresh=None):
        super().__init__(parent)
        self.on_close_refresh = on_close_refresh
        self.title("إدارة المخزون")
        set_window_icon(self)
        maximize_window(self)

        self._build_ui()
        self._refresh_table()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        tk.Label(self, text="إدارة المخزون", font=FONT_TITLE, fg=COLOR_PRIMARY).pack(pady=10)

        table_frame = ttk.Frame(self)
        table_frame.pack(fill="both", expand=True, padx=10)
        self.tree = make_treeview(
            table_frame,
            {
                "name": ("الصنف", 220),
                "qty": ("الكمية الحالية", 200),
                "threshold": ("حد التنبيه (كجم)", 150),
                "status": ("الحالة", 120),
            },
        )

        # --- حذف الصنف المحدد ---
        delete_btn = tk.Button(
            table_frame, text="🗑 حذف الصنف المحدد", font=FONT_NORMAL, bg="#fdecea", fg="#c0392b",
            command=self._delete_selected_product,
        )
        delete_btn.pack(pady=8)

        # --- إضافة نوع جديد ---
        add_frame = ttk.LabelFrame(self, text="إضافة نوع جديد")
        add_frame.pack(fill="x", padx=15, pady=8)
        _, self.new_name_entry = labeled_entry(add_frame, "اسم/تركيز الصنف:", 0, col=2)
        _, self.new_threshold_entry = labeled_entry(add_frame, "حد التنبيه (كجم):", 0, col=0)
        tk.Button(
            add_frame, text="➕ إضافة الصنف", font=FONT_NORMAL, command=self._add_product
        ).grid(row=0, column=4, padx=10)

        # --- توريد/شراء كمية ---
        supply_frame = ttk.LabelFrame(self, text="توريد / شراء كمية جديدة")
        supply_frame.pack(fill="x", padx=15, pady=8)

        ttk.Label(supply_frame, text="الصنف:", font=FONT_NORMAL).grid(row=0, column=3, padx=5, pady=5)
        self.supply_product_combo = ttk.Combobox(supply_frame, font=FONT_NORMAL, width=20, state="readonly")
        self.supply_product_combo.grid(row=0, column=2, padx=5)

        _, self.supply_qty_entry = labeled_entry(supply_frame, "الكمية (كجم):", 0, col=0)
        _, self.supply_price_entry = labeled_entry(supply_frame, "سعر الشراء/كجم:", 1, col=0)

        tk.Button(
            supply_frame, text="✅ تسجيل التوريد", font=FONT_NORMAL,
            command=self._supply_stock,
        ).grid(row=0, column=4, rowspan=2, padx=10)

        # --- تعديل حد التنبيه ---
        threshold_frame = ttk.LabelFrame(self, text="تعديل حد التنبيه لنوع محدد")
        threshold_frame.pack(fill="x", padx=15, pady=8)

        ttk.Label(threshold_frame, text="الصنف:", font=FONT_NORMAL).grid(row=0, column=3, padx=5, pady=5)
        self.threshold_product_combo = ttk.Combobox(threshold_frame, font=FONT_NORMAL, width=20, state="readonly")
        self.threshold_product_combo.grid(row=0, column=2, padx=5)

        _, self.threshold_entry = labeled_entry(threshold_frame, "الحد الجديد (كجم):", 0, col=0)
        tk.Button(
            threshold_frame, text="حفظ", font=FONT_NORMAL, command=self._update_threshold
        ).grid(row=0, column=4, padx=10)

    # ---------------------------------------------------------------
    def _refresh_table(self):
        clear_treeview(self.tree)
        products = inventory_service.list_products()
        for p in products:
            status = "⚠ منخفض" if p.is_below_alert else "طبيعي"
            self.tree.insert(
                "", "end",
                values=(p.name, inventory_service.format_quantity(p.current_quantity_kg),
                        format_number(p.alert_threshold_kg), status),
            )
        names = [p.name for p in products]
        self.supply_product_combo.config(values=names)
        self.threshold_product_combo.config(values=names)
        self._products_by_name = {p.name: p for p in products}

    def _add_product(self):
        name = self.new_name_entry.get().strip()
        if not name:
            show_error("أدخل اسم الصنف")
            return
        try:
            threshold = float(self.new_threshold_entry.get() or 0)
        except ValueError:
            show_error("حد التنبيه لازم يكون رقم")
            return
        try:
            inventory_service.add_product(name, threshold)
        except Exception as e:
            show_error(f"تعذر إضافة الصنف (ربما موجود بالفعل): {e}")
            return
        self.new_name_entry.delete(0, tk.END)
        self.new_threshold_entry.delete(0, tk.END)
        self._refresh_table()
        if self.on_close_refresh:
            self.on_close_refresh()

    def _supply_stock(self):
        name = self.supply_product_combo.get()
        product = self._products_by_name.get(name)
        if not product:
            show_error("اختر الصنف أولاً")
            return
        try:
            qty = float(self.supply_qty_entry.get())
            price = float(self.supply_price_entry.get())
        except ValueError:
            show_error("الكمية والسعر يجب أن يكونا أرقام")
            return
        try:
            inventory_service.record_stock_in(product.id, qty, price)
        except ValueError as e:
            show_error(str(e))
            return
        self._show_success(f"تم توريد {format_number(qty)} كجم من {product.name} بنجاح")
        self.supply_qty_entry.delete(0, tk.END)
        self.supply_price_entry.delete(0, tk.END)

        self._refresh_table()

        if self.on_close_refresh:
            self.on_close_refresh()

    def _update_threshold(self):
        name = self.threshold_product_combo.get()
        product = self._products_by_name.get(name)
        if not product:
            show_error("اختر الصنف أولاً")
            return
        try:
            new_threshold = float(self.threshold_entry.get())
        except ValueError:
            show_error("أدخل رقم صحيح")
            return
        inventory_service.update_alert_threshold(product.id, new_threshold)
        show_info("تم تحديث حد التنبيه")
        self.threshold_entry.delete(0, tk.END)
        self._refresh_table()
        if self.on_close_refresh:
            self.on_close_refresh()

    def _delete_selected_product(self):
        selected = self.tree.selection()
        if not selected:
            show_error("اختر الصنف اللي عايز تحذفه أولاً من الجدول")
            return

        name = self.tree.item(selected[0], "values")[0]  # أول عمود في الجدول هو الاسم
        product = self._products_by_name.get(name)
        if not product:
            show_error("تعذر تحديد الصنف")
            return

        if not confirm(
            f"هل أنت متأكد من حذف '{product.name}'؟\n"
            "لن يظهر بعد كده في شاشة البيع أو المخزون، لكن الفواتير القديمة\n"
            "اللي فيها هيفضل محفوظة زي ما هي في التقارير."
        ):
            return

        inventory_service.deactivate_product(product.id)
        self._show_success(f"تم حذف '{product.name}' بنجاح")
        self._refresh_table()
        if self.on_close_refresh:
            self.on_close_refresh()

    def _show_success(self, message):
        if hasattr(self, "_success_label") and self._success_label.winfo_exists():
            self._success_label.destroy()

        self._success_label = tk.Label(
            self,
            text="✓ " + message,
            font=("Segoe UI", 11, "bold"),
            bg="#1e8c4a",
            fg="white",
            padx=15,
            pady=7
        )

        self._success_label.place(
            relx=0.5,
            rely=0.96,
            anchor="center"
        )

        self.after(2500, self._hide_success)

    def _hide_success(self):
        if hasattr(self, "_success_label") and self._success_label.winfo_exists():
            self._success_label.destroy()

    def _on_close(self):
        if self.on_close_refresh:
            self.on_close_refresh()
        self.destroy()


class PricingWindow(tk.Toplevel):
    """
    شاشة السعر الثابت للبيع لكل نوع - سعر ثابت تقدر تعدّله وقت ما
    السعر في السوق يتغير، مش لازم تدخله كل يوم من الأول.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.title("السعر الثابت للبيع")
        set_window_icon(self)
        maximize_window(self)
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        tk.Label(self, text="السعر الثابت للبيع لكل نوع", font=FONT_TITLE, fg=COLOR_PRIMARY).pack(pady=10)
        tk.Label(
            self, text="عدّل السعر هنا فقط لو السعر في السوق اتغيّر - مش لازم تدخله كل يوم.",
            font=FONT_NORMAL, fg="#555",
        ).pack(pady=(0, 10))

        table_frame = ttk.Frame(self)
        table_frame.pack(fill="both", expand=True, padx=10)
        self.tree = make_treeview(
            table_frame,
            {"name": ("الصنف", 220), "price": ("السعر الحالي/كجم", 180), "date": ("آخر تعديل", 150)},
            height=8,
        )

        entry_frame = ttk.LabelFrame(self, text="تعديل السعر")
        entry_frame.pack(fill="x", padx=15, pady=10)

        ttk.Label(entry_frame, text="الصنف:", font=FONT_NORMAL).grid(row=0, column=3, padx=5, pady=8)
        self.product_combo = ttk.Combobox(entry_frame, font=FONT_NORMAL, width=20, state="readonly")
        self.product_combo.grid(row=0, column=2, padx=5)

        _, self.price_entry = labeled_entry(entry_frame, "السعر الجديد/كجم:", 0, col=0)

        tk.Button(
            entry_frame, text="💾 حفظ السعر", font=FONT_BOLD, command=self._save_price
        ).grid(row=0, column=4, padx=10)

    def _refresh(self):
        clear_treeview(self.tree)
        products = inventory_service.list_products()
        for p in products:
            price = pricing_service.get_current_price(p.id)
            history = pricing_service.get_price_history(p.id)
            date_str = history[0]["date"] if history else "-"
            price_display = format_number(price) if price is not None else "لم يُحدد بعد"
            self.tree.insert("", "end", values=(p.name, price_display, date_str))
        self.product_combo.config(values=[p.name for p in products])
        self._products_by_name = {p.name: p for p in products}

    def _show_success(self, message):
        if hasattr(self, "_success_label") and self._success_label.winfo_exists():
            self._success_label.destroy()

        self._success_label = tk.Label(
            self,
            text="✓ " + message,
            font=("Segoe UI", 11, "bold"),
            bg="#1e8c4a",
            fg="white",
            padx=15,
            pady=7
        )

        self._success_label.place(
            relx=0.5,
            rely=0.93,
            anchor="center"
        )

        self.after(2500, self._hide_success)

    def _hide_success(self):
        if hasattr(self, "_success_label") and self._success_label.winfo_exists():
            self._success_label.destroy()

    def _save_price(self):
        name = self.product_combo.get()
        product = self._products_by_name.get(name)
        if not product:
            show_error("اختر الصنف أولاً")
            return
        try:
            price = float(self.price_entry.get())
        except ValueError:
            show_error("أدخل سعر صحيح")
            return
        try:
            pricing_service.set_price(product.id, price, auth_manager.current_employee.id)
        except ValueError as e:
            show_error(str(e))
            return
        self._show_success("تم حفظ السعر بنجاح")

        self.price_entry.delete(0, tk.END)
        self._refresh()
"""
الشاشة الرئيسية (لوحة التحكم)
================================
بتظهر بعد تسجيل الدخول. القائمة بقت شريط جانبي ثابت على اليمين (زي
تصميم "فان أرينا")، وفيه كل الأقسام مرتبة فوق بعض بأيقونة واسم واضح،
بدل شبكة أزرار كبيرة. المحتوى الرئيسي بيعرض ترحيب وتنبيهات المخزون.

كل قسم (شاشة) ليه نسخة واحدة بس مفتوحة في نفس الوقت: لو ضغطت على نفس
البند في القائمة وهو مفتوح بالفعل، بينقلها لقدامك بدل ما يفتح نسخة
جديدة منها.
"""

import tkinter as tk
from tkinter import ttk

from auth.auth_manager import auth_manager
from config import STORE_NAME
from services import inventory_service, backup_service
from gui.widgets.common import (
    FONT_TITLE, FONT_BOLD, FONT_NORMAL, COLOR_PRIMARY, COLOR_DANGER,
    show_info, show_error,
)
from utils.ui_helpers import set_window_icon, maximize_window, load_logo_image

SIDEBAR_WIDTH = 300
SIDEBAR_BG = "#16324f"          # كحلي غامق للشريط الجانبي
SIDEBAR_BG_HOVER = "#20456f"     # أفتح شوية عند تمرير الماوس
SIDEBAR_BG_ACTIVE = "#1e5b8c"    # لون العنصر المفتوح حالياً
SIDEBAR_TEXT = "#e8eef5"
SIDEBAR_TEXT_MUTED = "#9fb3c8"
CONTENT_BG = "#f4f6f8"


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{STORE_NAME} - الشاشة الرئيسية")
        self.configure(bg=CONTENT_BG)
        set_window_icon(self)
        maximize_window(self)

        self._open_windows = {}   # key -> نسخة الشاشة المفتوحة حالياً (شاشة واحدة لكل بند)
        self._nav_rows = {}       # key -> (row_frame, icon_label, text_label) لتلوين البند النشط

        self._build_ui()
        self._check_low_stock()

    # ---------------------------------------------------------------
    def _build_ui(self):
        # الشريط الجانبي على اليمين (ثابت طول الوقت)
        sidebar = tk.Frame(self, bg=SIDEBAR_BG, width=SIDEBAR_WIDTH)
        sidebar.pack(side="right", fill="y")
        sidebar.pack_propagate(False)

        self._build_sidebar_header(sidebar)
        self._build_sidebar_nav(sidebar)
        self._build_sidebar_footer(sidebar)

        # منطقة المحتوى الرئيسية على الشمال
        content = tk.Frame(self, bg=CONTENT_BG)
        content.pack(side="left", fill="both", expand=True)
        self._build_content(content)

    # ---------------------------------------------------------------
    def _build_sidebar_header(self, sidebar):
        header = tk.Frame(sidebar, bg=SIDEBAR_BG)
        header.pack(fill="x", pady=(25, 15))

        self._logo_image = load_logo_image(max_size=64)
        if self._logo_image is not None:
            tk.Label(header, image=self._logo_image, bg=SIDEBAR_BG).pack(pady=(0, 8))

        tk.Label(
            header, text=STORE_NAME, font=FONT_BOLD, bg=SIDEBAR_BG, fg=SIDEBAR_TEXT,
            wraplength=SIDEBAR_WIDTH - 30, justify="center",
        ).pack(padx=10)

        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", padx=15, pady=(15, 5))

        emp = auth_manager.current_employee
        role_ar = "مدير" if emp.is_manager else "موظف"
        user_frame = tk.Frame(sidebar, bg=SIDEBAR_BG)
        user_frame.pack(fill="x", pady=(5, 15))
        tk.Label(
            user_frame, text=f"👤 {emp.name}", font=FONT_NORMAL, bg=SIDEBAR_BG, fg=SIDEBAR_TEXT,
        ).pack()
        tk.Label(
            user_frame, text=f"({role_ar})", font=("Segoe UI", 9), bg=SIDEBAR_BG, fg=SIDEBAR_TEXT_MUTED,
        ).pack()

    def _build_sidebar_nav(self, sidebar):
        nav_container = tk.Frame(sidebar, bg=SIDEBAR_BG)
        nav_container.pack(fill="both", expand=True)

        emp = auth_manager.current_employee
        nav_items = []
        if auth_manager.has_permission("sales"):
            nav_items.append(("sales", "🧾", "فاتورة بيع جديدة", self._open_sales))
        if auth_manager.has_permission("inventory_manage"):
            nav_items.append(("inventory", "📦", "إدارة المخزون", self._open_inventory))
        if auth_manager.has_permission("pricing_manage"):
            nav_items.append(("pricing", "💰", "السعر الثابت للبيع", self._open_pricing))
        if auth_manager.has_permission("customers_manage"):
            nav_items.append(("customers", "👥", "حسابات العملاء", self._open_customers))
        if auth_manager.has_permission("reports_view"):
            nav_items.append(("reports", "📊", "التقارير", self._open_reports))
        if emp.is_manager:
            nav_items.append(("employees", "🔑", "الموظفين والصلاحيات", self._open_employees))

        if not nav_items:
            tk.Label(
                nav_container,
                text="لا توجد صلاحيات إضافية مفعّلة\nلحسابك حالياً.\nتواصل مع المدير.",
                font=FONT_NORMAL, bg=SIDEBAR_BG, fg=SIDEBAR_TEXT_MUTED, justify="center",
            ).pack(pady=30, padx=15)

        for key, icon, label, command in nav_items:
            self._add_nav_row(nav_container, key, icon, label, command)

    def _add_nav_row(self, parent, key, icon, label, command):
        row = tk.Frame(parent, bg=SIDEBAR_BG, cursor="hand2")
        row.pack(fill="x")

        icon_label = tk.Label(row, text=icon, font=("Segoe UI", 14), bg=SIDEBAR_BG, fg=SIDEBAR_TEXT, width=3)
        icon_label.pack(side="right", padx=(5, 10), pady=14)

        text_label = tk.Label(
            row, text=label, font=FONT_NORMAL, bg=SIDEBAR_BG, fg=SIDEBAR_TEXT, anchor="e",
            wraplength=SIDEBAR_WIDTH - 70, justify="right",
        )
        text_label.pack(side="right", fill="x", expand=True, padx=(5, 5), pady=14)

        self._nav_rows[key] = (row, icon_label, text_label)

        widgets = (row, icon_label, text_label)

        def on_enter(_e):
            if self._nav_rows[key][0].cget("bg") != SIDEBAR_BG_ACTIVE:
                for w in widgets:
                    w.configure(bg=SIDEBAR_BG_HOVER)

        def on_leave(_e):
            if self._nav_rows[key][0].cget("bg") != SIDEBAR_BG_ACTIVE:
                for w in widgets:
                    w.configure(bg=SIDEBAR_BG)

        def on_click(_e):
            self._set_active_nav(key)
            command()

        for w in widgets:
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>", on_click)

    def _set_active_nav(self, active_key):
        """يلوّن بند القائمة المفتوح حالياً بلون مختلف عشان تعرف انت واقف فين."""
        for key, (row, icon_label, text_label) in self._nav_rows.items():
            bg = SIDEBAR_BG_ACTIVE if key == active_key else SIDEBAR_BG
            for w in (row, icon_label, text_label):
                w.configure(bg=bg)

    def _build_sidebar_footer(self, sidebar):
        footer = tk.Frame(sidebar, bg=SIDEBAR_BG)
        footer.pack(fill="x", side="bottom", pady=15)

        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", side="bottom", padx=15, pady=5)

        tk.Button(
            footer, text="💾  نسخة احتياطية الآن", font=FONT_NORMAL, bg=SIDEBAR_BG, fg=SIDEBAR_TEXT,
            activebackground=SIDEBAR_BG_HOVER, activeforeground=SIDEBAR_TEXT, bd=0, anchor="e",
            command=self._do_backup,
        ).pack(fill="x", padx=15, pady=4)

        tk.Button(
            footer, text="🚪  تسجيل الخروج", font=FONT_NORMAL, bg=SIDEBAR_BG, fg="#ff8a80",
            activebackground=SIDEBAR_BG_HOVER, activeforeground="#ff8a80", bd=0, anchor="e",
            command=self._logout,
        ).pack(fill="x", padx=15, pady=4)

    # ---------------------------------------------------------------
    def _build_content(self, content):
        header = tk.Frame(content, bg=CONTENT_BG)
        header.pack(fill="x", padx=30, pady=(25, 10))

        emp = auth_manager.current_employee
        tk.Label(
            header, text=f"أهلاً بيك، {emp.name} 👋", font=FONT_TITLE, bg=CONTENT_BG, fg=COLOR_PRIMARY,
        ).pack(anchor="e")
        tk.Label(
            header, text="اختار قسم من القائمة على اليمين للبدء.", font=FONT_NORMAL,
            bg=CONTENT_BG, fg="#666",
        ).pack(anchor="e", pady=(4, 0))

        # منطقة التنبيهات
        self.alerts_frame = tk.Frame(content, bg=CONTENT_BG)
        self.alerts_frame.pack(fill="x", padx=30)

        credit_label = tk.Label(
        content,
        text="[01069483389]  |  [01228223180]  |  تطوير: [م/أحمد حاتم]",
        font=("Segoe UI", 9),
        bg=CONTENT_BG,
        fg="#999999",
    )
        credit_label.pack(side="bottom", anchor="w", padx=20, pady=15)

    # ---------------------------------------------------------------
    def _check_low_stock(self):
        for widget in self.alerts_frame.winfo_children():
            widget.destroy()

        low_products = inventory_service.get_low_stock_products()
        if not low_products:
            return

        names = "، ".join(p.name for p in low_products)
        alert_box = tk.Frame(self.alerts_frame, bg="#fdecea", highlightbackground="#f5c6cb", highlightthickness=1)
        alert_box.pack(fill="x", pady=15)
        tk.Label(
            alert_box,
            text=f"⚠ تنبيه: وصلت هذه الأنواع للحد الأدنى من المخزون: {names}",
            fg=COLOR_DANGER,
            bg="#fdecea",
            font=FONT_NORMAL,
            wraplength=900,
            justify="right",
        ).pack(padx=15, pady=12, anchor="e")

    # ---------------------------------------------------------------
    def _show_singleton(self, key, factory):
        """
        يفتح شاشة واحدة بس لكل بند في القائمة. لو الشاشة مفتوحة بالفعل
        بيرجعها لقدام (lift/focus) بدل ما يفتح نسخة تانية منها.
        """
        existing = self._open_windows.get(key)
        if existing is not None and existing.winfo_exists():
            existing.lift()
            existing.focus_force()
            return

        window = factory()
        self._open_windows[key] = window

        def on_destroy(e, k=key):
            # الحدث ده بيتولّد لكل عنصر جوه الشاشة وقت ما تتقفل، مش للشاشة
            # نفسها بس - فبنتجاهل أي حدث غير خاص بالنافذة ذاتها.
            if e.widget is not window:
                return
            # وقت إغلاق الشاشة الرئيسية نفسها (تسجيل خروج أو إغلاق البرنامج)،
            # كل الشاشات الفرعية بتتقفل تلقائياً معاها، فمن الممكن عناصر
            # القائمة الجانبية تكون اتقفلت هي كمان قبل ما الحدث ده يوصل -
            # نتجاهل الخطأ ده بهدوء لأنه مجرد إعادة تلوين شكلي مش أكتر.
            try:
                if not self.winfo_exists():
                    return
                if k in self._nav_rows:
                    self._set_active_nav(None)
            except tk.TclError:
                pass

        window.bind("<Destroy>", on_destroy)

    def _open_sales(self):
        from gui.sales_window import SalesWindow
        self._show_singleton("sales", lambda: SalesWindow(self, on_close_refresh=self._check_low_stock))

    def _open_inventory(self):
        from gui.inventory_window import InventoryWindow
        self._show_singleton("inventory", lambda: InventoryWindow(self, on_close_refresh=self._check_low_stock))

    def _open_pricing(self):
        from gui.inventory_window import PricingWindow
        self._show_singleton("pricing", lambda: PricingWindow(self))

    def _open_customers(self):
        from gui.customers_window import CustomersWindow
        self._show_singleton("customers", lambda: CustomersWindow(self))

    def _open_reports(self):
        from gui.reports_window import ReportsWindow
        self._show_singleton("reports", lambda: ReportsWindow(self))

    def _open_employees(self):
        if not auth_manager.is_manager():
            show_error("هذه الشاشة للمدير فقط")
            return
        from gui.employees_window import EmployeesWindow
        self._show_singleton("employees", lambda: EmployeesWindow(self))

    def _do_backup(self):
        try:
            path = backup_service.create_backup()
            show_info(f"تم عمل نسخة احتياطية بنجاح:\n{path}")
        except Exception as e:
            show_error(str(e))

    def _logout(self):
        auth_manager.logout()
        self.destroy()
        from gui.login_window import LoginWindow
        from main import launch_main_window
        LoginWindow(on_success=launch_main_window).mainloop()

"""
شاشة تسجيل الدخول
====================
أول شاشة تظهر عند فتح البرنامج. بعد نجاح الدخول تفتح الشاشة الرئيسية.
"""

import tkinter as tk
from tkinter import ttk

from auth.auth_manager import auth_manager
from gui.widgets.common import FONT_TITLE, FONT_NORMAL, COLOR_PRIMARY, show_error
from utils.ui_helpers import set_window_icon, load_logo_image


class LoginWindow(tk.Tk):
    def __init__(self, on_success):
        super().__init__()
        self.on_success = on_success
        self.title("تسجيل الدخول - برنامج بيع ماء النار")
        self.geometry("420x460")
        self.configure(bg="#ffffff")
        self.resizable(False, False)
        set_window_icon(self)

        self._build_ui()
        self.bind("<Return>", lambda e: self._try_login())

    def _build_ui(self):
        container = ttk.Frame(self)
        container.pack(expand=True)

        self._logo_image = load_logo_image(max_size=110)
        if self._logo_image is not None:
            tk.Label(container, image=self._logo_image, bg="#ffffff").grid(
                row=0, column=0, columnspan=2, pady=(20, 5)
            )

        title = tk.Label(
            container, text="تسجيل الدخول", font=FONT_TITLE, fg=COLOR_PRIMARY, bg="#ffffff"
        )
        title.grid(row=1, column=0, columnspan=2, pady=(5, 20))

        ttk.Label(container, text="اسم المستخدم:", font=FONT_NORMAL).grid(
            row=2, column=1, sticky="e", padx=8, pady=8
        )
        self.username_entry = ttk.Entry(container, font=FONT_NORMAL, width=22)
        self.username_entry.grid(row=2, column=0, sticky="w", padx=8, pady=8)

        ttk.Label(container, text="كلمة المرور:", font=FONT_NORMAL).grid(
            row=3, column=1, sticky="e", padx=8, pady=8
        )
        self.password_entry = ttk.Entry(container, font=FONT_NORMAL, width=22, show="*")
        self.password_entry.grid(row=3, column=0, sticky="w", padx=8, pady=8)

        self.error_label = tk.Label(container, text="", fg="red", bg="#ffffff", font=FONT_NORMAL)
        self.error_label.grid(row=4, column=0, columnspan=2, pady=(5, 5))

        login_btn = tk.Button(
            container,
            text="دخول",
            font=FONT_NORMAL,
            bg=COLOR_PRIMARY,
            fg="white",
            width=18,
            command=self._try_login,
        )
        login_btn.grid(row=5, column=0, columnspan=2, pady=15)

        self.username_entry.focus_set()
        # --- هامش الشاشة: بيانات المطوّر ---
        footer = tk.Label(
            self,
            text="[01069483389]  |  [01228223180]  |  تطوير: [م/أحمد حاتم]",
            font=("Segoe UI", 9),
            bg="#ffffff",
            fg="#999999",
        )
        footer.pack(side="bottom", pady=12)
    def _try_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:
            self.error_label.config(text="من فضلك أدخل اسم المستخدم وكلمة المرور")
            return

        success, message = auth_manager.login(username, password)
        if success:
            self.destroy()
            self.on_success()
        else:
            self.error_label.config(text=message)
            self.password_entry.delete(0, tk.END)

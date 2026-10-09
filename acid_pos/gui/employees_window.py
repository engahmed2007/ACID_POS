"""
شاشة إدارة الموظفين والصلاحيات (للمدير فقط)
===============================================
المدير عنده كل الصلاحيات دايماً. لأي موظف عادي، المدير يقدر يحدد
بالظبط أي شاشات/عمليات مسموح له يدخلها من نفس الشاشة دي.
"""

import tkinter as tk
from tkinter import ttk

from auth.permissions import PERMISSION_DEFINITIONS
from services import employee_service
from gui.widgets.common import (
    FONT_TITLE, FONT_BOLD, FONT_NORMAL, COLOR_PRIMARY,
    make_treeview, clear_treeview, show_error, show_info, labeled_entry, confirm,
)
from utils.ui_helpers import set_window_icon, maximize_window


class EmployeesWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("إدارة الموظفين والصلاحيات")
        set_window_icon(self)
        maximize_window(self)

        self._permission_vars = {}  # key -> BooleanVar لصلاحيات الموظف المحدد حالياً

        self._build_ui()
        self._refresh()

    def _build_ui(self):
        tk.Label(self, text="إدارة الموظفين والصلاحيات", font=FONT_TITLE, fg=COLOR_PRIMARY).pack(pady=10)

        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=15)

        # --- يسار: جدول الموظفين ---
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))

        self.tree = make_treeview(
            left_frame,
            {
                "name": ("الاسم", 160), "username": ("اسم المستخدم", 130),
                "role": ("الصلاحية", 90), "status": ("الحالة", 90),
            },
        )
        self.tree.bind("<<TreeviewSelect>>", self._on_select_employee)

        action_frame = ttk.Frame(left_frame)
        action_frame.pack(fill="x", pady=8)
        tk.Button(action_frame, text="تعطيل الحساب المحدد", font=FONT_NORMAL,
                  command=self._deactivate_selected).pack(side="right", padx=8)
        tk.Button(action_frame, text="تفعيل الحساب المحدد", font=FONT_NORMAL,
                  command=self._activate_selected).pack(side="right", padx=8)

        pw_frame = ttk.LabelFrame(left_frame, text="تغيير كلمة مرور الموظف المحدد")
        pw_frame.pack(fill="x", pady=8)
        _, self.new_password_entry = labeled_entry(pw_frame, "كلمة المرور الجديدة:", 0, col=0, show="*")
        tk.Button(pw_frame, text="حفظ", font=FONT_NORMAL, command=self._change_password).grid(row=0, column=2, padx=10)

        add_frame = ttk.LabelFrame(left_frame, text="إضافة موظف جديد")
        add_frame.pack(fill="x", pady=8)
        _, self.name_entry = labeled_entry(add_frame, "الاسم:", 0, col=4)
        _, self.username_entry = labeled_entry(add_frame, "اسم المستخدم:", 0, col=2)
        _, self.password_entry = labeled_entry(add_frame, "كلمة المرور:", 0, col=0, show="*")

        self.role_var = tk.StringVar(value="employee")
        ttk.Radiobutton(add_frame, text="موظف عادي", value="employee", variable=self.role_var).grid(row=1, column=0)
        ttk.Radiobutton(add_frame, text="مدير", value="manager", variable=self.role_var).grid(row=1, column=1)

        tk.Button(add_frame, text="➕ إضافة", font=FONT_NORMAL, command=self._add_employee).grid(
            row=0, column=5, padx=10
        )

        # --- يمين: صلاحيات الموظف المحدد ---
        right_frame = ttk.LabelFrame(main_frame, text="صلاحيات الموظف المحدد")
        right_frame.pack(side="left", fill="y", padx=(10, 0))

        self.selected_employee_label = tk.Label(
            right_frame, text="اختر موظف من القائمة", font=FONT_BOLD, fg=COLOR_PRIMARY,
        )
        self.selected_employee_label.pack(pady=(10, 5), padx=10)

        self.permissions_container = ttk.Frame(right_frame)
        self.permissions_container.pack(padx=10, pady=5, fill="x")

        for key, label in PERMISSION_DEFINITIONS.items():
            var = tk.BooleanVar(value=False)
            self._permission_vars[key] = var
            cb = ttk.Checkbutton(self.permissions_container, text=label, variable=var)
            cb.pack(anchor="e", pady=3, fill="x")

        self.save_permissions_btn = tk.Button(
            right_frame, text="💾 حفظ الصلاحيات", font=FONT_BOLD,
            command=self._save_permissions, state="disabled",
        )
        self.save_permissions_btn.pack(pady=15, padx=10)

        tk.Label(
            right_frame,
            text="ملحوظة: حساب المدير عنده كل الصلاحيات\nتلقائياً بغض النظر عن هذه القائمة.",
            font=FONT_NORMAL, fg="#777", justify="right",
        ).pack(pady=(0, 10), padx=10)

    def _refresh(self):
        clear_treeview(self.tree)
        self._employees = employee_service.list_employees()
        for e in self._employees:
            role_ar = "مدير" if e.role == "manager" else "موظف"
            status = "نشط" if e.is_active else "معطل"
            self.tree.insert("", "end", values=(e.name, e.username, role_ar, status))
        self._selected_employee = None
        self._set_permissions_enabled(False)

    def _get_selected_employee(self):
        selected = self.tree.selection()
        if not selected:
            return None
        values = self.tree.item(selected[0], "values")
        username = values[1]
        return next((e for e in self._employees if e.username == username), None)

    # ---------------------------------------------------------------
    def _on_select_employee(self, event=None):
        emp = self._get_selected_employee()
        self._selected_employee = emp
        if emp is None:
            self._set_permissions_enabled(False)
            return

        role_ar = "مدير" if emp.role == "manager" else "موظف"
        self.selected_employee_label.config(text=f"{emp.name} ({role_ar})")

        for key, var in self._permission_vars.items():
            var.set(key in emp.permissions)

        # المدير عنده كل الصلاحيات تلقائياً، فمفيش داعي يعدّل صلاحيات مفصّلة له
        self._set_permissions_enabled(not emp.is_manager)

    def _set_permissions_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for child in self.permissions_container.winfo_children():
            child.configure(state=state)
        self.save_permissions_btn.configure(state=state)

    def _save_permissions(self):
        if self._selected_employee is None:
            show_error("اختر موظف أولاً")
            return
        selected_permissions = {key for key, var in self._permission_vars.items() if var.get()}
        employee_service.update_permissions(self._selected_employee.id, selected_permissions)
        show_info(f"تم حفظ صلاحيات {self._selected_employee.name} بنجاح")
        self._refresh()

    # ---------------------------------------------------------------
    def _add_employee(self):
        name = self.name_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        role = self.role_var.get()

        if not name or not username or not password:
            show_error("من فضلك أدخل كل البيانات")
            return
        if employee_service.username_exists(username):
            show_error("اسم المستخدم موجود بالفعل")
            return

        employee_service.create_employee(name, username, password, role)
        show_info("تم إضافة الموظف بنجاح. حدد اسمه من القائمة لضبط صلاحياته.")
        self.name_entry.delete(0, tk.END)
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
        self._refresh()

    def _deactivate_selected(self):
        emp = self._get_selected_employee()
        if not emp:
            show_error("اختر موظف أولاً")
            return
        if not confirm(f"هل تريد تعطيل حساب {emp.name}؟"):
            return
        employee_service.deactivate_employee(emp.id)
        self._refresh()

    def _activate_selected(self):
        emp = self._get_selected_employee()
        if not emp:
            show_error("اختر موظف أولاً")
            return
        employee_service.activate_employee(emp.id)
        self._refresh()

    def _change_password(self):
        emp = self._get_selected_employee()
        if not emp:
            show_error("اختر موظف أولاً")
            return
        new_password = self.new_password_entry.get()
        if not new_password:
            show_error("أدخل كلمة مرور جديدة")
            return
        employee_service.change_password(emp.id, new_password)
        show_info(f"تم تغيير كلمة مرور {emp.name}")
        self.new_password_entry.delete(0, tk.END)

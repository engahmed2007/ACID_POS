"""
دوال وعناصر مساعدة مشتركة بين شاشات الواجهة
==============================================
"""

import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry

from utils.formatting import format_number, format_money, format_quantity  # noqa: F401 (يعاد تصديرها)

# ألوان أساسية للتطبيق
COLOR_BG = "#f4f6f8"
COLOR_PRIMARY = "#1e5b8c"
COLOR_DANGER = "#c0392b"
COLOR_SUCCESS = "#1e8c4a"
FONT_NORMAL = ("Segoe UI", 11)
FONT_BOLD = ("Segoe UI", 12, "bold")
FONT_TITLE = ("Segoe UI", 16, "bold")



def make_treeview(parent, columns: dict, height: int = 12) -> ttk.Treeview:
    """
    columns: dict {عمود_id: (عنوان, عرض)}
    بترجع Treeview جاهز مع scrollbar.
    """
    frame = ttk.Frame(parent)
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    tree = ttk.Treeview(frame, columns=list(columns.keys()), show="headings", height=height)
    for col_id, (title, width) in columns.items():
        tree.heading(col_id, text=title)
        tree.column(col_id, width=width, anchor="center")

    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    tree.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")
    return tree


def clear_treeview(tree: ttk.Treeview):
    for row in tree.get_children():
        tree.delete(row)


def show_error(message: str):
    messagebox.showerror("خطأ", message)


def show_info(message: str):
    messagebox.showinfo("تنبيه", message)


def confirm(message: str) -> bool:
    return messagebox.askyesno("تأكيد", message)


def labeled_entry(parent, label_text: str, row: int, col: int = 0, width: int = 22, show=None):
    """يرجع (label, entry) بعد وضعهم في الشبكة (grid)."""
    label = ttk.Label(parent, text=label_text, font=FONT_NORMAL)
    label.grid(row=row, column=col, sticky="e", padx=5, pady=6)
    entry = ttk.Entry(parent, width=width, font=FONT_NORMAL, show=show)
    entry.grid(row=row, column=col + 1, sticky="w", padx=5, pady=6)
    return label, entry


def date_picker(parent, label_text: str, row: int, col: int = 0, initial_date=None):
    """
    يرجع (label, DateEntry) بعد وضعهم في الشبكة - حقل تاريخ بشكل تقويم
    يقدر المستخدم يختار منه بالماوس بدل ما يكتب التاريخ يدوي.
    القيمة النهائية بصيغة YYYY-MM-DD (متوافقة مع كل استعلامات قاعدة البيانات).
    """
    label = ttk.Label(parent, text=label_text, font=FONT_NORMAL)
    label.grid(row=row, column=col, sticky="e", padx=5, pady=6)
    entry = DateEntry(
        parent, width=16, font=FONT_NORMAL, date_pattern="yyyy-mm-dd",
        background=COLOR_PRIMARY, foreground="white", borderwidth=2,
        locale="ar",
    )
    if initial_date is not None:
        entry.set_date(initial_date)
    entry.grid(row=row, column=col + 1, sticky="w", padx=5, pady=6)
    return label, entry

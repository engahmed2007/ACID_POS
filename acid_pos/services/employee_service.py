"""
خدمة إدارة الموظفين
======================
إنشاء/تعطيل موظفين وتغيير كلمات المرور. كل الدوال دي المفروض تتنادى
بس من شاشة إدارة الموظفين اللي بتتحقق إن المستخدم الحالي "مدير".
"""

from database.db_manager import db
from models.models import Employee
from auth.auth_manager import create_employee, hash_new_password  # noqa: F401 (يعاد تصديرها)
from auth.permissions import permissions_from_string, permissions_to_string


def list_employees(active_only: bool = False) -> list[Employee]:
    query = "SELECT * FROM employees"
    if active_only:
        query += " WHERE is_active = 1"
    query += " ORDER BY name"
    rows = db.fetch_all(query)
    return [
        Employee(
            id=r["id"], name=r["name"], username=r["username"],
            role=r["role"], is_active=bool(r["is_active"]),
            permissions=permissions_from_string(r["permissions"]),
        )
        for r in rows
    ]


def update_permissions(employee_id: int, permissions: set):
    """تحديث صلاحيات موظف معين. المدير هو الوحيد المسموح له بمناداة هذه الدالة."""
    db.execute(
        "UPDATE employees SET permissions = ? WHERE id = ?",
        (permissions_to_string(permissions), employee_id),
    )


def deactivate_employee(employee_id: int):
    db.execute("UPDATE employees SET is_active = 0 WHERE id = ?", (employee_id,))


def activate_employee(employee_id: int):
    db.execute("UPDATE employees SET is_active = 1 WHERE id = ?", (employee_id,))


def change_password(employee_id: int, new_password: str):
    password_hash, salt_hex = hash_new_password(new_password)
    db.execute(
        "UPDATE employees SET password_hash = ?, password_salt = ? WHERE id = ?",
        (password_hash, salt_hex, employee_id),
    )


def username_exists(username: str) -> bool:
    row = db.fetch_one("SELECT COUNT(*) as c FROM employees WHERE username = ?", (username,))
    return row["c"] > 0

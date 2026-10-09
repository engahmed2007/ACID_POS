"""
إدارة تسجيل الدخول وكلمات المرور
==================================
- كلمة المرور بتتخزن مشفرة (PBKDF2-HMAC-SHA256) مع "ملح" (salt) عشوائي
  مختلف لكل مستخدم، مش نص عادي أبداً.
- في نسخة واحدة من "المستخدم الحالي" (current session) طول ما البرنامج شغال.
"""

import hashlib
import os
import secrets

from config import PASSWORD_HASH_ITERATIONS
from database.db_manager import db
from models.models import Employee
from auth.permissions import permissions_from_string, permissions_to_string, DEFAULT_EMPLOYEE_PERMISSIONS


def _hash_password(password: str, salt: bytes) -> str:
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_HASH_ITERATIONS
    )
    return dk.hex()


def hash_new_password(password: str):
    """بترجع (password_hash, salt) جاهزين للتخزين في قاعدة البيانات."""
    salt = secrets.token_bytes(16)
    return _hash_password(password, salt), salt.hex()


def verify_password(password: str, stored_hash: str, stored_salt_hex: str) -> bool:
    salt = bytes.fromhex(stored_salt_hex)
    candidate_hash = _hash_password(password, salt)
    return secrets.compare_digest(candidate_hash, stored_hash)


class AuthManager:
    """يحتفظ بالموظف الذي سجّل دخوله حالياً (Session بسيطة)."""

    def __init__(self):
        self.current_employee: Employee | None = None

    def login(self, username: str, password: str) -> tuple[bool, str]:
        row = db.fetch_one(
            "SELECT * FROM employees WHERE username = ? AND is_active = 1",
            (username,),
        )
        if row is None:
            return False, "اسم المستخدم غير موجود أو الحساب معطل"

        if not verify_password(password, row["password_hash"], row["password_salt"]):
            return False, "كلمة المرور غير صحيحة"

        self.current_employee = Employee(
            id=row["id"],
            name=row["name"],
            username=row["username"],
            role=row["role"],
            is_active=bool(row["is_active"]),
            permissions=permissions_from_string(row["permissions"]),
        )
        return True, "تم تسجيل الدخول بنجاح"

    def logout(self):
        self.current_employee = None

    def is_logged_in(self) -> bool:
        return self.current_employee is not None

    def is_manager(self) -> bool:
        return self.is_logged_in() and self.current_employee.is_manager

    def has_permission(self, permission_key: str) -> bool:
        """
        المدير عنده كل الصلاحيات تلقائياً. الموظف العادي لازم يكون
        المدير فعّل له الصلاحية دي بالتحديد من شاشة إدارة الموظفين.
        """
        if not self.is_logged_in():
            return False
        if self.current_employee.is_manager:
            return True
        return permission_key in self.current_employee.permissions


# نسخة واحدة مشتركة لكل البرنامج
auth_manager = AuthManager()


def create_employee(name: str, username: str, password: str, role: str = "employee",
                     permissions: set = None) -> int:
    """إنشاء موظف جديد. يستخدمها مدير النظام فقط من شاشة الموظفين."""
    password_hash, salt_hex = hash_new_password(password)
    if permissions is None:
        permissions = set(DEFAULT_EMPLOYEE_PERMISSIONS) if role == "employee" else set()
    return db.execute(
        """INSERT INTO employees (name, username, password_hash, password_salt, role, permissions)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (name, username, password_hash, salt_hex, role, permissions_to_string(permissions)),
    )


def ensure_default_manager():
    """
    لو مفيش أي موظفين في قاعدة البيانات (أول تشغيل للبرنامج)،
    ينشئ حساب مدير افتراضي عشان تقدر تدخل أول مرة.
    اسم المستخدم: admin | كلمة المرور: admin123
    (لازم تتغير فوراً من شاشة إدارة الموظفين بعد أول دخول)
    """
    row = db.fetch_one("SELECT COUNT(*) as c FROM employees")
    if row["c"] == 0:
        create_employee("مدير النظام", "admin", "admin123", role="manager")
        return True
    return False

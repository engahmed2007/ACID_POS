"""
مدير الاتصال بقاعدة البيانات
=============================
كل التعامل المباشر مع SQLite (فتح اتصال، تنفيذ أوامر، تحميل المخطط)
محصور في الملف ده بس. باقي البرنامج (الشاشات والخدمات) بيتعامل مع
دوال جاهزة زي `execute` و `fetch_all` و `fetch_one`، ومش بيعرف حاجة
عن SQLite نفسها.

ليه الموضوع ده مهم؟
لو حبينا مستقبلاً ننقل من SQLite لـ PostgreSQL (عشان أكتر من جهاز
يشتغلوا على نفس البيانات في نفس الوقت)، هنغير الملف ده بس، وباقي
البرنامج (الشاشات، التقارير...) هيفضل شغال زي ما هو من غير أي تعديل،
لأن كل حاجة بتتكلم مع هذه الطبقة فقط، مش مع SQLite مباشرة.
"""

import sqlite3
import os
import threading

from config import DATABASE_PATH, SCHEMA_SQL_PATH


class DatabaseManager:
    """
    طبقة وصول للبيانات (Data Access Layer).
    - Singleton بسيط: اتصال واحد يتشارك فيه كل البرنامج (مناسب لتطبيق سطح مكتب).
    - thread-safe بشكل أساسي عن طريق قفل (Lock) حول كل عملية كتابة.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, db_path: str = DATABASE_PATH):
        if getattr(self, "_initialized", False):
            return
        self.db_path = db_path
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._initialized = True
        self._load_schema()

    def _load_schema(self):
        with open(SCHEMA_SQL_PATH, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        with self._lock:
            self._conn.executescript(schema_sql)
            self._conn.commit()
        self._run_migrations()

    def _run_migrations(self):
        """
        تعديلات بسيطة على جداول موجودة من نسخة قديمة من البرنامج (لو حد
        عنده قاعدة بيانات اتنشأت قبل إضافة عمود معين). كل تعديل محاط
        بمحاولة/تجاهل الخطأ عشان ميأثرش لو العمود موجود بالفعل.
        """
        migrations = [
            "ALTER TABLE employees ADD COLUMN permissions TEXT NOT NULL DEFAULT ''",
            "ALTER TABLE invoices ADD COLUMN subtotal_amount REAL NOT NULL DEFAULT 0",
            "ALTER TABLE invoices ADD COLUMN discount_amount REAL NOT NULL DEFAULT 0",
            "ALTER TABLE customers ADD COLUMN code TEXT",
        ]
        with self._lock:
            for statement in migrations:
                try:
                    self._conn.execute(statement)
                    self._conn.commit()
                except sqlite3.OperationalError:
                    pass  # العمود موجود بالفعل، من نسخة أحدث

            # تعبئة كود لأي عميل قديم اتسجل قبل إضافة هذا العمود
            try:
                rows = self._conn.execute(
                    "SELECT id FROM customers WHERE code IS NULL"
                ).fetchall()
                for row in rows:
                    self._conn.execute(
                        "UPDATE customers SET code = ? WHERE id = ?",
                        (f"C{row[0]:04d}", row[0]),
                    )
                self._conn.commit()
            except sqlite3.OperationalError:
                pass

    # ---------- عمليات عامة ----------

    def execute(self, query: str, params: tuple = ()) -> int:
        """
        لتنفيذ أوامر التعديل (INSERT/UPDATE/DELETE).
        بترجع lastrowid (مفيد بعد الـ INSERT).
        """
        with self._lock:
            cur = self._conn.execute(query, params)
            self._conn.commit()
            return cur.lastrowid

    def executemany(self, query: str, seq_of_params) -> None:
        with self._lock:
            self._conn.executemany(query, seq_of_params)
            self._conn.commit()

    def fetch_all(self, query: str, params: tuple = ()):
        cur = self._conn.execute(query, params)
        return cur.fetchall()

    def fetch_one(self, query: str, params: tuple = ()):
        cur = self._conn.execute(query, params)
        return cur.fetchone()

    def executescript(self, script: str) -> None:
        with self._lock:
            self._conn.executescript(script)
            self._conn.commit()

    @property
    def connection(self):
        return self._conn

    def close(self):
        self._conn.close()


# نسخة واحدة مشتركة تستخدمها كل الملفات
db = DatabaseManager()

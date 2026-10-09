"""
إعدادات عامة للبرنامج
=====================
كل الإعدادات الثابتة (مسارات، اسم قاعدة البيانات، الخ) في مكان واحد
عشان لو حبينا نغيرها مستقبلاً منغيرش غير هنا بس.

فرق مهم بين نوعين من الملفات (خصوصاً لو البرنامج اتحول لملف .exe
باستخدام PyInstaller):

1. ملفات "قراءة فقط" (الأيقونة، الشعار، مخطط قاعدة البيانات) - دي بتترحّل
   جوه الملف التنفيذي نفسه وقت التحزيم، فلازم نلاقيها بـ resource_path()
   اللي بيدور في مجلد PyInstaller المؤقت (sys._MEIPASS) وقت التشغيل
   كملف .exe، أو في مجلد المشروع العادي وقت التشغيل كسكريبت بايثون.

2. ملفات "قراءة وكتابة" (قاعدة البيانات، النسخ الاحتياطية، ملفات التصدير)
   - دي لازم تتحفظ بجانب الملف التنفيذي نفسه (مش جوه المجلد المؤقت اللي
   بيتمسح بعد قفل البرنامج)، فبتستخدم data_path() اللي بيدور بجانب
   sys.executable وقت التشغيل كملف .exe.
"""

import os
import sys


def resource_path(relative_path: str) -> str:
    """
    مسار لملف "قراءة فقط" مرفق مع البرنامج (أيقونة، شعار، schema.sql).
    وقت التشغيل كملف .exe مبني بـ PyInstaller، الملفات دي بتكون متحزمة
    جوه مجلد مؤقت (sys._MEIPASS). وقت التشغيل كسكريبت بايثون عادي،
    بيدور في مجلد المشروع نفسه.
    """
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def data_path(relative_path: str) -> str:
    """
    مسار لملف "قراءة وكتابة" لازم يفضل موجود بعد قفل البرنامج (قاعدة
    البيانات، النسخ الاحتياطية، التصدير). وقت التشغيل كملف .exe، بيتحفظ
    بجانب الـ .exe نفسه (sys.executable) مش في مجلد مؤقت بيتمسح. وقت
    التشغيل كسكريبت بايثون عادي، بيتحفظ في مجلد المشروع نفسه.
    """
    if getattr(sys, "frozen", False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


# مجلد البيانات (قاعدة البيانات + النسخ الاحتياطية + التصدير) - قراءة وكتابة
DATA_DIR = data_path("data")
os.makedirs(DATA_DIR, exist_ok=True)

# ملف قاعدة البيانات
DATABASE_PATH = os.path.join(DATA_DIR, "acid_pos.db")

# مجلد النسخ الاحتياطية
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

# مجلد تصدير التقارير
EXPORTS_DIR = os.path.join(DATA_DIR, "exports")
os.makedirs(EXPORTS_DIR, exist_ok=True)

# حد التحويل من كيلو لطن (لعرض الكمية بالطن لو كبيرة)
KG_PER_TON = 1000

# الحد اللي لو الكمية زادت عليه نعرضها بالطن بدل الكيلو في الشاشات
TON_DISPLAY_THRESHOLD_KG = 1000

# عدد مرات تكرار التشفير لكلمة المرور (كل ما زاد رقم أمان أكتر لكن أبطأ شوية)
PASSWORD_HASH_ITERATIONS = 200_000

# اسم الشركة/المحل يظهر في رأس الفاتورة المطبوعة
STORE_NAME = "محل بيع ماء النار بالجملة والقطاعي"

# ملفات الشعار وأيقونة البرنامج ومخطط قاعدة البيانات - قراءة فقط (مرفقة مع البرنامج)
ASSETS_DIR = resource_path("assets")
ICON_ICO_PATH = os.path.join(ASSETS_DIR, "icon.ico")
LOGO_PNG_PATH = os.path.join(ASSETS_DIR, "logo.png")
SCHEMA_SQL_PATH = resource_path(os.path.join("database", "schema.sql"))

"""
خدمة النسخ الاحتياطي
=======================
نسخ ملف قاعدة البيانات كامل لمجلد النسخ الاحتياطية باسم فيه التاريخ والوقت.
ينفع كزرار يدوي في البرنامج، أو يتنادى تلقائي عند إغلاق البرنامج.
"""

import shutil
import os
from datetime import datetime

from config import DATABASE_PATH, BACKUP_DIR


def create_backup() -> str:
    """يعمل نسخة احتياطية الآن، وبيرجع مسار الملف الجديد."""
    if not os.path.exists(DATABASE_PATH):
        raise FileNotFoundError("ملف قاعدة البيانات غير موجود")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"acid_pos_backup_{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    shutil.copy2(DATABASE_PATH, backup_path)
    return backup_path


def list_backups() -> list[str]:
    if not os.path.exists(BACKUP_DIR):
        return []
    files = [f for f in os.listdir(BACKUP_DIR) if f.endswith(".db")]
    files.sort(reverse=True)
    return files


def cleanup_old_backups(keep_last: int = 30):
    """يحتفظ بآخر عدد معين من النسخ الاحتياطية بس، ويحذف الأقدم."""
    files = list_backups()
    for old_file in files[keep_last:]:
        try:
            os.remove(os.path.join(BACKUP_DIR, old_file))
        except OSError:
            pass

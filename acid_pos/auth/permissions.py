"""
تعريف الصلاحيات القابلة للتحكم فيها من المدير
=================================================
المدير (role = 'manager') عنده كل الصلاحيات دايماً بشكل تلقائي، ومش
محتاج أي تفعيل يدوي. الصلاحيات هنا خاصة بالموظف العادي بس، والمدير
هو اللي بيحددها لكل موظف من شاشة "إدارة الموظفين".

ملحوظة: إدارة الموظفين نفسها (إضافة/تعطيل موظفين، تعديل صلاحياتهم)
مقصورة على المدير فقط دايماً، ومش من ضمن الصلاحيات القابلة للتفويض،
حفاظاً على أمان النظام.
"""

# key -> الاسم المعروض في الواجهة
PERMISSION_DEFINITIONS = {
    "sales": "تسجيل فواتير بيع جديدة",
    "inventory_manage": "إدارة المخزون (إضافة أنواع / توريد كميات / حدود التنبيه)",
    "pricing_manage": "تعديل السعر الثابت للبيع",
    "customers_manage": "حسابات العملاء (إضافة عميل / تسجيل دفعات)",
    "reports_view": "عرض التقارير",
    "invoices_delete": "حذف الفواتير",
}

# الصلاحيات الافتراضية لأي موظف جديد يتم إنشاؤه (المدير يقدر يغيّرها بعد كده)
DEFAULT_EMPLOYEE_PERMISSIONS = {"sales"}


def permissions_to_string(permissions: set) -> str:
    return ",".join(sorted(p for p in permissions if p in PERMISSION_DEFINITIONS))


def permissions_from_string(text: str) -> set:
    if not text:
        return set()
    return {p for p in text.split(",") if p in PERMISSION_DEFINITIONS}

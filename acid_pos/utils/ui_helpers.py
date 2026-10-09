"""
أدوات مساعدة للواجهة: الأيقونة، وضع ملء الشاشة، وتحميل الشعار
================================================================
مكان واحد لكل هذه الأمور عشان كل شاشة تستخدمها بنفس الطريقة بالظبط.
"""

import tkinter as tk

from config import ICON_ICO_PATH, LOGO_PNG_PATH


def set_window_icon(window):
    """
    يحط أيقونة البرنامج على الشاشة (شريط العنوان / شريط المهام).
    بيجرب ملف .ico الأول (بيشتغل تمام على ويندوز)، ولو فشل (زي أنظمة
    لينكس/ماك اللي مش بتدعم .ico) بيستخدم نسخة PNG بديلة، وبيتجاهل
    أي خطأ بهدوء عشان الشاشة تفتح عادي حتى لو الأيقونة مش متاحة.
    """
    try:
        window.iconbitmap(ICON_ICO_PATH)
        return
    except Exception:
        pass
    try:
        icon_img = tk.PhotoImage(file=LOGO_PNG_PATH)
        window.iconphoto(True, icon_img)
        window._icon_ref = icon_img  # نحتفظ بمرجع عشان الصورة متتمسحش من الذاكرة
    except Exception:
        pass


def maximize_window(window):
    """
    يفتح الشاشة في وضع ملء الشاشة (Full Screen) مع الحفاظ على شريط
    العنوان وأزرار التصغير/التكبير/الإغلاق (على عكس '-fullscreen' اللي
    بتشيل شريط العنوان بالكامل).
    """
    try:
        window.state("zoomed")  # يشتغل على ويندوز وأغلب بيئات لينكس
        return
    except tk.TclError:
        pass
    try:
        window.attributes("-zoomed", True)  # بعض بيئات لينكس (X11)
        return
    except tk.TclError:
        pass
    # كحل أخير: نجبر حجم الشاشة يبقى بحجم الشاشة الفعلي
    screen_w = window.winfo_screenwidth()
    screen_h = window.winfo_screenheight()
    window.geometry(f"{screen_w}x{screen_h}+0+0")


def load_logo_image(max_size: int = 140):
    """
    يحمّل صورة الشعار (PNG) ويصغّرها لحجم مناسب لعرضها كشعار داخل
    الشاشات. من غير أي مكتبات خارجية (زي Pillow) - بيستخدم subsample
    المدمجة في Tkinter نفسها، وبترجع None بهدوء لو الصورة مش موجودة.
    """
    try:
        img = tk.PhotoImage(file=LOGO_PNG_PATH)
        w, h = img.width(), img.height()
        if w <= 0 or h <= 0:
            return img
        factor = max(1, round(max(w, h) / max_size))
        if factor > 1:
            img = img.subsample(factor, factor)
        return img
    except Exception:
        return None

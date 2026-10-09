"""
نقطة تشغيل البرنامج
======================
شغّل هذا الملف عشان تفتح البرنامج: `python main.py`
"""

from auth.auth_manager import ensure_default_manager
from gui.login_window import LoginWindow


def launch_main_window():
    from gui.main_window import MainWindow
    MainWindow().mainloop()


def main():
    ensure_default_manager()
    LoginWindow(on_success=launch_main_window).mainloop()


if __name__ == "__main__":
    main()

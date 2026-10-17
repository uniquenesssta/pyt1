import os

def enable_windows_dpi_awareness() -> None:
    """让 Tkinter 在 Windows 高分屏上更清晰。"""
    if os.name != "nt":
        return
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass



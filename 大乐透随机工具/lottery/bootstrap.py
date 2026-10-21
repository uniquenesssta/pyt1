"""启动、Windows DPI 与异常日志。"""
import ctypes
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys
import tkinter as tk
from tkinter import messagebox
from .ui.app import LotteryApp


def main():
    if sys.platform == "win32":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass
    root = tk.Tk()
    root.withdraw()
    try:
        data_dir = Path(__file__).resolve().parent.parent / "user_data"
        data_dir.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(data_dir / "app.log", maxBytes=1_000_000, backupCount=2, encoding="utf-8")
        logging.basicConfig(handlers=[handler], level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
        app = LotteryApp(root, data_dir)

        def report(kind, value, tb):
            logging.error("界面回调失败", exc_info=(kind, value, tb))
            app.error(value)
        root.report_callback_exception = report
        root.deiconify()
        root.mainloop()
    except Exception as error:
        logging.exception("启动失败")
        messagebox.showerror("大乐透随机工具启动失败", str(error), parent=root)
        root.destroy()


if __name__ == "__main__":
    main()

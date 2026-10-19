"""组装窗口、摇卦控制器与错误处理。"""
import tkinter as tk

from .startup.errors import show_exception
from .ui.casting import CastingController
from .ui.window import LiuYaoWindow


def main():
    root = tk.Tk()
    try:
        root.report_callback_exception = show_exception
        view = LiuYaoWindow(root)
        controller = CastingController(root, view)
        view.bind_start(controller.start)
        root.protocol("WM_DELETE_WINDOW", controller.close)
        root.mainloop()
    finally:
        try:
            root.destroy()
        except tk.TclError:
            pass

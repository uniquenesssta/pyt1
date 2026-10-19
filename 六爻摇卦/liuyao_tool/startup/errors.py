"""pythonw 没有控制台时仍可看到异常。"""
import ctypes
import os
import sys
import traceback


def show_exception(exc_type, exc_value, exc_traceback):
    details = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    if os.name == "nt":
        ctypes.windll.user32.MessageBoxW(
            None,
            "程序运行出错，请截图保留以下信息：\n\n" + details[-3500:],
            "六爻摇卦 · 错误",
            0x10,
        )
    elif sys.stderr is not None:
        sys.stderr.write(details)

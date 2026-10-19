"""无控制台模式的启动异常展示。"""
import ctypes
import os
import traceback


def run():
    try:
        from app import main
        main()
    except Exception:
        detail = traceback.format_exc()
        if os.name == "nt":
            ctypes.windll.user32.MessageBoxW(
                None, "程序启动失败，请截图保留以下错误：\n\n" + detail,
                "字体批量改名", 0x10,
            )
        else:
            raise

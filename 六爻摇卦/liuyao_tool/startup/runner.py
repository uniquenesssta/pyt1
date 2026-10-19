"""统一捕获导入、Tk 初始化和主窗口启动异常。"""
import sys

from .errors import show_exception


def run():
    try:
        from ..application import main
        main()
    except Exception:
        show_exception(*sys.exc_info())
        return 1
    return 0

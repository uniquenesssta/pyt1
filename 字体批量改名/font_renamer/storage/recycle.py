"""只提供 Windows 回收站操作，不降级为永久删除。"""
import os


def recycle_file(path):
    if os.name != 'nt':
        raise RuntimeError('回收站清理仅支持 Windows')
    try:
        from send2trash.win.modern import send2trash
    except ImportError as exc:
        raise RuntimeError('缺少回收站依赖，请重新运行 install.bat') from exc
    send2trash(os.path.abspath(path))

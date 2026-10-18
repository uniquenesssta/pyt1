"""Run without a console and report otherwise invisible startup failures."""
import ctypes
import traceback
from pathlib import Path


def run():
    try:
        from app import main
        main()
    except Exception:
        details = traceback.format_exc()
        log = Path(__file__).resolve().parents[2] / 'data' / 'startup-error.log'
        try:
            log.parent.mkdir(parents=True, exist_ok=True)
            log.write_text(details, encoding='utf-8')
            message = f'程序启动失败。错误详情已保存到：\n{log}\n\n{details[-1800:]}'
        except OSError:
            message = f'程序启动失败，错误日志无法保存：\n{details[-1800:]}'
        ctypes.windll.user32.MessageBoxW(None, message, '开业场景强随机生成器', 0x10)
        return 1
    return 0

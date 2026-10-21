"""预览项实际文件定位与单文件回收站清理。"""
from pathlib import Path
from ..config import STATUS_DONE


def preview_file_path(plan):
    # 成功改名后使用新路径；失败时不猜测临时文件或其他目标。
    path = plan.new_path if plan.status == STATUS_DONE else plan.old_path
    if not path:
        raise ValueError('此项没有可删除的文件路径')
    return str(Path(path).absolute())


def delete_preview_file(plan, recycle):
    path = preview_file_path(plan)
    if not Path(path).is_file() or Path(path).is_symlink():
        raise ValueError('文件不存在、不是普通文件或为符号链接，请重新扫描')
    recycle(path)
    return path

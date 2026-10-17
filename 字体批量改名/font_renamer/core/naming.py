import os
import re
import unicodedata
from typing import Iterable
from ..config import WINDOWS_RESERVED_NAMES

def normalize_path(path: str) -> str:
    """用于冲突判断的路径标准化。Windows 下大小写不敏感。"""
    return os.path.normcase(os.path.abspath(path))


def parse_int_list(text: str, default: Iterable[int]) -> list[int]:
    """支持输入：4,1,16,6 或 0x0804,0x0409,0。"""
    text = text.strip()
    if not text:
        return list(default)

    items = re.split(r"[，,\s;；]+", text)
    values: list[int] = []
    for item in items:
        item = item.strip()
        if not item:
            continue
        values.append(int(item, 0))
    if not values or any(v < 0 or v > 65535 for v in values):
        raise ValueError("优先级必须包含 0–65535 之间的整数")
    return list(dict.fromkeys(values))


def sanitize_filename(name: str, *, use_underscore: bool = True, max_length: int = 180) -> str:
    """清理字符串，使其成为 Windows/macOS/Linux 上更安全的文件名。"""
    if name is None:
        name = ""

    name = unicodedata.normalize("NFKC", str(name))
    name = name.replace("\u200b", "")
    name = re.sub(r"[<>:\"/\\|?*]", "_", name)
    name = re.sub(r"[\x00-\x1f]", "", name)
    name = name.strip(". ")

    if use_underscore:
        name = re.sub(r"\s+", "_", name)
        name = re.sub(r"_+", "_", name)
    else:
        name = re.sub(r"\s+", " ", name)

    name = name.strip(". _") if use_underscore else name.strip(". ")

    if not name:
        name = "Untitled_Font"

    # 避免 Windows 保留文件名，例如 CON.ttf、PRN.otf。
    if name.split(".", 1)[0].upper() in WINDOWS_RESERVED_NAMES:
        name = f"_{name}"

    if len(name) > max_length:
        name = name[:max_length].rstrip(". _")

    return name or "Untitled_Font"



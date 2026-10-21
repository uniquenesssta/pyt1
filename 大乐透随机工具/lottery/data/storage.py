"""工具私有文件的原子写入和收藏持久化。"""
import json
import os
from pathlib import Path
import tempfile
from ..core.models import Ticket


def atomic_write(path, text, encoding="utf-8"):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding=encoding, newline="",
                                         dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


class FavoriteStore:
    def __init__(self, path):
        self.path = Path(path)

    def load(self):
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if data.get("version") != 1 or not isinstance(data.get("tickets"), list):
                raise ValueError("不支持的收藏文件格式")
            return list(dict.fromkeys(Ticket(tuple(t["front"]), tuple(t["back"])) for t in data["tickets"]))
        except (ValueError, TypeError, KeyError, AttributeError) as error:
            raise ValueError(f"收藏文件损坏，原文件未覆盖：{self.path}\n{error}") from error

    def save(self, tickets):
        payload = {"version": 1, "tickets": [{"front": t.front, "back": t.back} for t in tickets]}
        atomic_write(self.path, json.dumps(payload, ensure_ascii=False, indent=2))

"""用原有收藏文件保存号码，并为新条目附加时间。"""
from datetime import datetime
import json
from pathlib import Path

from ..core.favorites import FavoriteRecord
from ..core.models import Ticket
from .storage import atomic_write


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
            records = {}
            for row in data["tickets"]:
                ticket = Ticket(tuple(row["front"]), tuple(row["back"]))
                value = row.get("saved_at")
                saved_at = datetime.fromisoformat(value) if value is not None else None
                records.setdefault(ticket, FavoriteRecord(ticket, saved_at))
            return list(records.values())
        except (ValueError, TypeError, KeyError, AttributeError) as error:
            raise ValueError(f"收藏文件损坏，原文件未覆盖：{self.path}\n{error}") from error

    def save(self, records):
        tickets = []
        for record in records:
            row = {"front": record.ticket.front, "back": record.ticket.back}
            if record.saved_at is not None:
                row["saved_at"] = record.saved_at.isoformat()
            tickets.append(row)
        atomic_write(self.path, json.dumps({"version": 1, "tickets": tickets}, ensure_ascii=False, indent=2))

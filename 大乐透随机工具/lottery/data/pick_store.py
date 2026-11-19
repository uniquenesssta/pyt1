"""选号及对奖记录单独保存在本机。"""
from datetime import date, datetime
import json
from pathlib import Path

from ..core.models import Ticket
from ..core.pick_records import PickRecord
from .storage import atomic_write


class PickStore:
    def __init__(self, path):
        self.path = Path(path)

    def load(self):
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if data["version"] != 1 or not isinstance(data["records"], list):
                raise ValueError("不支持的选号记录格式")
            return [
                PickRecord(Ticket(tuple(row["front"]), tuple(row["back"])),
                           datetime.fromisoformat(row["saved_at"]),
                           date.fromisoformat(row["target_date"]), row.get("issue", ""))
                for row in data["records"]
            ]
        except (ValueError, TypeError, KeyError, AttributeError) as error:
            raise ValueError(f"选号记录无法读取，原文件保留：{self.path}\n{error}") from error

    def save(self, records):
        payload = {"version": 1, "records": [
            {"front": r.ticket.front, "back": r.ticket.back,
             "saved_at": r.saved_at.isoformat(timespec="seconds"),
             "target_date": r.target_date.isoformat(), "issue": r.issue}
            for r in records
        ]}
        atomic_write(self.path, json.dumps(payload, ensure_ascii=False, indent=2))

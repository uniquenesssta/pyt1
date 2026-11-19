"""收藏时间和去重；旧条目可以没有时间。"""
from dataclasses import dataclass
from datetime import datetime

from .draw_calendar import BEIJING, beijing_time
from .models import Ticket


@dataclass(frozen=True)
class FavoriteRecord:
    ticket: Ticket
    saved_at: datetime | None = None

    def __post_init__(self):
        if self.saved_at is not None:
            object.__setattr__(self, "saved_at", beijing_time(self.saved_at))


def new_favorites(records, tickets, saved_at):
    existing = {record.ticket for record in records}
    return [FavoriteRecord(ticket, saved_at) for ticket in dict.fromkeys(tickets)
            if ticket not in existing]


def newest_first(records):
    undated = datetime.min.replace(tzinfo=BEIJING)
    return sorted(records, key=lambda record: record.saved_at or undated, reverse=True)

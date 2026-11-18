"""持久化选号记录的字段和按期去重规则。"""
from dataclasses import dataclass
from datetime import date, datetime

from .draw_calendar import beijing_time, expected_draw_date
from .draw_index import issue_key
from .models import Ticket


@dataclass(frozen=True)
class PickRecord:
    ticket: Ticket
    saved_at: datetime
    target_date: date
    issue: str = ""

    def __post_init__(self):
        object.__setattr__(self, "saved_at", beijing_time(self.saved_at))
        if not isinstance(self.issue, str):
            raise ValueError("选号记录期号格式错误")
        if self.issue:
            object.__setattr__(self, "issue", issue_key(self.issue))

    @classmethod
    def from_selection(cls, ticket, now):
        return cls(ticket, now, expected_draw_date(now))


def existing_pick(records, pick, history):
    """同一期的相同号码只记一次；手动改到别期后可在本期另记。"""
    for record in reversed(records):
        if record.ticket != pick.ticket:
            continue
        if record.issue:
            draw, _ = history.resolve(record)
            if draw is not None and draw.draw_date == pick.target_date.isoformat():
                return record
        elif record.target_date == pick.target_date:
            return record
    return None

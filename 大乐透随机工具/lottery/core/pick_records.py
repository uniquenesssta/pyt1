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
    index = _period_positions(records, {pick.ticket}, pick.target_date, history).get(pick.ticket)
    return None if index is None else records[index]


def _period_positions(records, tickets, target_date, history):
    positions = {}
    for index, record in enumerate(records):
        if record.ticket not in tickets:
            continue
        if record.issue:
            draw, _ = history.resolve(record)
            matches = draw is not None and draw.draw_date == target_date.isoformat()
        else:
            matches = record.target_date == target_date
        if matches:
            positions[record.ticket] = index
    return positions


def prepare_pick_batch(records, tickets, now, history):
    """同批用同一次记录时间；返回新增记录及全部选中号码对应的索引。"""
    tickets = dict.fromkeys(tickets)
    target_date = expected_draw_date(now)
    existing = _period_positions(records, tickets, target_date, history)
    additions, indices = [], []
    for ticket in tickets:
        if ticket in existing:
            indices.append(existing[ticket])
        else:
            indices.append(len(records) + len(additions))
            additions.append(PickRecord(ticket, now, target_date))
    return additions, indices, target_date

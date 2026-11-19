"""用连续期号建立历史参照；缺期时断开，避免错误的跨期数据。"""
from dataclasses import dataclass
from datetime import date, timedelta

from .draw_calendar import DRAW_WEEKDAYS
from .draw_index import issue_key
from .history_window import ordered_history, window_start
from .models import check_cancel
from .trend_indicators import FRONT


OMISSION_MINIMUM = 12


def consecutive(previous, current):
    if not (previous.issue and current.issue):
        return False
    a, b = issue_key(previous.issue), issue_key(current.issue)
    if previous.draw_date and current.draw_date and previous.draw_date >= current.draw_date:
        return False
    if len(a) == len(b) == 5:
        year_a, year_b = int(a[:2]), int(b[:2])
        seq_a, seq_b = int(a[2:]), int(b[2:])
        if year_a == year_b:
            return seq_a > 0 and seq_b == seq_a + 1
        if (year_b != year_a + 1 or seq_b != 1
                or not (previous.draw_date and current.draw_date)):
            return False
        # 跨年只接受紧接的常规开奖日；不能确认是否漏期时宁可不计。
        day = date.fromisoformat(previous.draw_date) + timedelta(days=1)
        while day.weekday() not in DRAW_WEEKDAYS:
            day += timedelta(days=1)
        return day.isoformat() == current.draw_date
    return len(a) == len(b) and int(b) == int(a) + 1


@dataclass(frozen=True)
class NumberReference:
    relation: tuple
    omission: tuple | None


@dataclass(frozen=True)
class PeriodReference:
    issue: str
    front: NumberReference
    back: NumberReference

    def zone(self, zone):
        return self.front if zone == FRONT else self.back


def _zone_reference(numbers, gaps, run):
    hits = set(numbers)
    neighbors = {n + delta for n in hits for delta in (-1, 1)} - hits
    relation = (-1,) + tuple(0 if n in hits else 1 if n in neighbors else 2 for n in range(1, len(gaps)))
    bands = (None if run < OMISSION_MINIMUM else
             (-1,) + tuple(0 if gap == 0 else 1 if gap <= 5 else 2 if gap <= 11 else 3 for gap in gaps[1:]))
    return NumberReference(relation, bands)


def scoped_references(draws, periods, cancel=None):
    ordered, order = ordered_history(draws)
    start = window_start(ordered, periods)
    references = {}
    previous, reference = None, None
    front_gaps, back_gaps = [0] * 36, [0] * 13
    run = 0
    for i in range(max(0, start - OMISSION_MINIMUM), len(ordered)):
        if i % 128 == 0:
            check_cancel(cancel)
        draw = ordered[i]
        adjacent = previous is not None and consecutive(previous, draw)
        if not adjacent:
            run = 0
            front_gaps, back_gaps = [0] * 36, [0] * 13
        elif i >= start:
            references[draw] = reference
        run += 1
        for numbers, gaps in ((draw.ticket.front, front_gaps), (draw.ticket.back, back_gaps)):
            for n in range(1, len(gaps)):
                gaps[n] = 0 if n in numbers else min(OMISSION_MINIMUM, gaps[n] + 1)
        reference = (PeriodReference(draw.issue, _zone_reference(draw.ticket.front, front_gaps, run),
                                     _zone_reference(draw.ticket.back, back_gaps, run)) if draw.issue else None)
        previous = draw
    check_cancel(cancel)
    return ordered[start:], order, references, reference

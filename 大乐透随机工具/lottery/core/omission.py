"""逐号遗漏：当前连缺和窗口内已完成间隔，缺期不拼接。"""
from dataclasses import dataclass

from .history_window import ordered_history, window_start
from .period_context import consecutive
from .trend_indicators import BACK, FRONT, ZONE_SIZES


@dataclass(frozen=True)
class OmissionRow:
    number: int
    current: int
    lower_bound: bool
    max_finished: int | None
    average_finished: float | None
    occurrences: int
    intervals: int
    last_seen: str


def omission_report(draws, periods):
    ordered, _ = ordered_history(draws)
    if not ordered[-1].issue:
        raise ValueError("没有期号，无法核实连续开奖")
    start = window_start(ordered, periods)
    segments = []
    for index, draw in enumerate(ordered):
        if index == 0 or not consecutive(ordered[index-1], draw):
            segments.append([])
        segments[-1].append((index, draw))

    result = {}
    for zone, (maximum, _) in ZONE_SIZES.items():
        hits = [0] * (maximum + 1)
        last_seen = [""] * (maximum + 1)
        intervals = [[] for _ in range(maximum + 1)]
        for segment in segments:
            latest = [None] * (maximum + 1)
            for i, draw in segment:
                numbers = draw.ticket.front if zone == FRONT else draw.ticket.back
                for n in numbers:
                    last_seen[n] = draw.issue
                    if i >= start:
                        hits[n] += 1
                        if latest[n] is not None and latest[n] >= start:
                            intervals[n].append(i - latest[n] - 1)
                    latest[n] = i
        result[zone] = tuple(
            OmissionRow(n, len(segments[-1]) if latest[n] is None else len(ordered)-1-latest[n],
                        latest[n] is None, max(intervals[n], default=None),
                        sum(intervals[n])/len(intervals[n]) if intervals[n] else None,
                        hits[n], len(intervals[n]), last_seen[n])
            for n in range(1, maximum + 1)
        )
    return result[FRONT], result[BACK], len(ordered)-start, len(segments[-1]), ordered[-1].issue

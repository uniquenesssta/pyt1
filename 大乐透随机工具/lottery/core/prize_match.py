"""比对前后区号码，按规则汇总普通单式或复式的各奖级注数。"""
from collections import Counter
from dataclasses import dataclass
from math import comb

from .draw_index import issue_key


# 2026-02-02 第26014期开始。旧期只比较号码，不套用新规则。
SEVEN_PRIZES = {
    (5, 2): 1, (5, 1): 2, (5, 0): 3, (4, 2): 3, (4, 1): 4,
    (4, 0): 5, (3, 2): 5, (3, 1): 6, (2, 2): 6,
    (3, 0): 7, (2, 1): 7, (1, 2): 7, (0, 2): 7,
}


@dataclass(frozen=True)
class PickMatch:
    front: tuple
    back: tuple
    prizes: tuple | None


def compare_pick(ticket, draw):
    front = tuple(n for n in ticket.front if n in draw.ticket.front)
    back = tuple(n for n in ticket.back if n in draw.ticket.back)
    issue = issue_key(draw.issue) if draw.issue else ""
    if len(issue) != 5 or int(issue) < 26014:
        return PickMatch(front, back, None)
    f, b = len(front), len(back)
    counts = Counter()
    for (front_hits, back_hits), level in SEVEN_PRIZES.items():
        combinations = (comb(f, front_hits) * comb(len(ticket.front) - f, 5 - front_hits)
                        * comb(b, back_hits) * comb(len(ticket.back) - b, 2 - back_hits))
        if combinations:
            counts[level] += combinations
    return PickMatch(front, back, tuple(sorted(counts.items())))

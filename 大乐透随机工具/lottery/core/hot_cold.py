"""近期号码频次：以同区号码平均出现次数区分冷热。"""
from collections import Counter
from dataclasses import dataclass
from .history_window import select_window


@dataclass(frozen=True)
class HotColdReport:
    requested: int
    total: int
    first: str
    last: str
    order: str
    front: tuple
    back: tuple


def number_rows(draws, area, maximum, slots):
    counts = Counter(n for d in draws for n in getattr(d.ticket, area))
    total = len(draws)
    rows = []
    for number in range(1, maximum+1):
        count = counts[number]
        # 用整数比较避免浮点误差；零次数也保留。
        difference = count * maximum - total * slots
        label = '热号' if difference > 0 else '冷号' if difference < 0 else '持平'
        rows.append((f'{number:02d}', count, f'{100*count/total:.2f}%', label))
    return tuple(sorted(rows, key=lambda row: (-row[1], row[0])))


def analyze_hot_cold(draws, periods=50):
    if periods not in (50,100): raise ValueError('冷热号窗口请选择50或100期')
    selected, order = select_window(draws, periods)
    first, last = selected[0], selected[-1]
    return HotColdReport(periods,len(selected),first.issue or str(first.line),last.issue or str(last.line),order,
                         number_rows(selected,'front',35,5),number_rows(selected,'back',12,2))

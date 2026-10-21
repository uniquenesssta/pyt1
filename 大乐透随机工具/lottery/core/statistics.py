"""一次遍历计算所有统计；比例分母在报表中显式区分。"""
from collections import Counter
from dataclasses import dataclass, field
from .features import features, zone
from .models import check_cancel


@dataclass
class Statistics:
    total: int = 0
    front: Counter = field(default_factory=Counter)
    back: Counter = field(default_factory=Counter)
    pairs: Counter = field(default_factory=Counter)
    zones: Counter = field(default_factory=Counter)
    empty: Counter = field(default_factory=Counter)
    intermediate: Counter = field(default_factory=Counter)
    max_span: Counter = field(default_factory=Counter)
    start_span: Counter = field(default_factory=Counter)
    runs: Counter = field(default_factory=Counter)
    gaps: list = field(default_factory=lambda: [Counter() for _ in range(4)])


def analyze(draws, cancel=None):
    result = Statistics()
    for i, draw in enumerate(draws):
        if i % 256 == 0:
            check_cancel(cancel)
        f = features(draw.ticket.front)
        result.total += 1
        result.front.update(draw.ticket.front)
        result.back.update(draw.ticket.back)
        result.pairs.update([draw.ticket.back])
        result.zones.update(zone(n) for n in draw.ticket.front)
        result.empty.update(f.empty_zones)
        result.intermediate.update(f.intermediate_zones)
        result.max_span.update([f.max_span])
        result.start_span.update([f.start_span])
        result.runs.update([f.longest_run])
        for counter, gap in zip(result.gaps, f.gaps):
            counter.update([gap])
    check_cancel(cancel)
    return result


def report_rows(stats):
    """类别、项目、次数、分母、百分比；零频号码也完整显示。"""
    rows = []

    def append(category, item, count, denominator):
        rows.append((category, str(item), count, denominator,
                     100 * count / denominator if denominator else 0.0))

    for label, counts, maximum, slots in [("前区", stats.front, 35, 5), ("后区", stats.back, 12, 2)]:
        for n in range(1, maximum + 1):
            append(label + "·期数占比", f"{n:02d}", counts[n], stats.total)
            append(label + "·号码频率", f"{n:02d}", counts[n], stats.total * slots)
    for pair, count in sorted(stats.pairs.items(), key=lambda x: (-x[1], x[0])):
        append("后区组合", " ".join(f"{n:02d}" for n in pair), count, stats.total)
    for z in range(1, 6):
        label = f"{z}区 ({(z-1)*7+1:02d}–{z*7:02d})"
        append("分区号码频率", label, stats.zones[z], stats.total * 5)
        append("空区", label, stats.empty[z], stats.total)
        append("差值>10覆盖中间区", label, stats.intermediate[z], stats.total)
    for span in range(5):
        append("最大跨区·相邻差>7", span, stats.max_span[span], stats.total)
        append("起始隐含跨区", span, stats.start_span[span], stats.total)
    for run in range(1, 6):
        append("最长连号·互斥", run, stats.runs[run], stats.total)
        if run >= 2:
            append("至少N连号·可重叠", run, sum(c for n, c in stats.runs.items() if n >= run), stats.total)
    for i, counter in enumerate(stats.gaps, 1):
        for gap in range(1, 32):
            append(f"C{i}相邻差值", gap, counter[gap], stats.total)
    return rows

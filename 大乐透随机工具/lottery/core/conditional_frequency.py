"""按上期单号或完整后区对子统计下一期，不跨过缺期。"""
from collections import Counter
from dataclasses import dataclass

from .draw_index import issue_key
from .history_window import ordered_history, window_start
from .models import Draw, check_cancel
from .period_context import consecutive


CONDITIONAL_MODE = "下期条件频次"
TOP_COUNT = 5


@dataclass(frozen=True)
class FrequencyRow:
    condition: tuple[int, ...]
    occurrences: int
    samples: int
    counts: tuple[int, ...]

    def ranking(self):
        return tuple(sorted(range(1, len(self.counts)), key=lambda n: (-self.counts[n], n)))

    @property
    def top(self):
        return tuple(n for n in self.ranking() if self.counts[n] > 0)[:TOP_COUNT]


@dataclass(frozen=True)
class ConditionalReport:
    anchor: Draw
    history_count: int
    first_issue: str
    front: tuple[FrequencyRow, ...]
    back: FrequencyRow

    @property
    def votes(self):
        return Counter(n for row in self.front for n in row.top)


def analyze_conditional_frequency(draws, anchor_issue="", periods=0, cancel=None):
    check_cancel(cancel)
    ordered, _ = ordered_history(draws)
    if not ordered[-1].issue:
        raise ValueError("下期条件频次需要带期号的开奖记录")
    if anchor_issue:
        key = issue_key(anchor_issue)
        index = next((i for i, draw in enumerate(ordered) if issue_key(draw.issue) == key), None)
        if index is None:
            raise ValueError(f"历史中找不到参照期 {anchor_issue}")
        ordered = ordered[:index+1]
    history = ordered[window_start(ordered, periods):]
    anchor = history[-1]
    conditions = anchor.ticket.front
    back_pair = anchor.ticket.back
    occurrences = Counter()
    samples = Counter()
    counts = {n: Counter() for n in conditions}
    back_occurrences = back_samples = 0
    back_counts = Counter()

    for i, draw in enumerate(history):
        if i % 128 == 0:
            check_cancel(cancel)
        matched = [n for n in conditions if n in draw.ticket.front]
        is_back = draw.ticket.back == back_pair
        occurrences.update(matched)
        back_occurrences += is_back
        if i+1 == len(history) or not consecutive(draw, history[i+1]):
            continue
        following = history[i+1].ticket
        samples.update(matched)
        for n in matched:
            counts[n].update(following.front)
        if is_back:
            back_samples += 1
            back_counts.update(following.back)
    check_cancel(cancel)

    return ConditionalReport(
        anchor, len(history), history[0].issue,
        tuple(FrequencyRow((n,), occurrences[n], samples[n], tuple(counts[n][k] for k in range(36)))
              for n in conditions),
        FrequencyRow(back_pair, back_occurrences, back_samples, tuple(back_counts[k] for k in range(13))),
    )


def conditional_weights(report, use_front=True, use_back=True):
    if not (use_front or use_back):
        raise ValueError("请选择前区或后区的条件频次")
    if use_front and not any(row.samples for row in report.front):
        raise ValueError("没有可用的前区连续期样本；请扩大窗口或取消前区加权")
    if use_back and not report.back.samples:
        raise ValueError("参照期后区整对没有可用的下一期样本；请扩大窗口或取消后区加权")
    votes = report.votes if use_front else Counter()
    front = {n: votes[n] + 1 for n in range(1, 36)}
    back = {n: report.back.counts[n] + 1 if use_back else 1 for n in range(1, 13)}
    return front, back

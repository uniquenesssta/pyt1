"""后区单式和复式的有限候选；复用每个 2 码对子的结构评分。"""
from bisect import bisect_right
from dataclasses import dataclass
from itertools import combinations

from .models import check_cancel
from .structure_profile import indicator_zone
from .structure_scoring import StructureScorer
from .trend_indicators import BACK
from .weighted import relative_cumulative


@dataclass(frozen=True)
class BackStructurePool:
    backs: tuple
    log_weights: tuple
    cumulative: tuple

    def choose(self, rng):
        index = bisect_right(self.cumulative, rng.random() * self.cumulative[-1])
        return self.backs[min(index, len(self.backs) - 1)]


def build_back_structure(pool, fixed, size, profile, selected, cancel=None):
    if profile is None or not any(indicator_zone(name) == BACK for name in selected):
        return None
    check_cancel(cancel)
    scorer = StructureScorer(profile, selected, BACK)
    pair_logs = {}
    for pair in combinations(sorted(fixed + pool), 2):
        score = scorer.log_weight(pair)
        if score is not None:
            pair_logs[pair] = score

    backs, logs_by_back = [], []
    for index, rest in enumerate(combinations(pool, size - len(fixed))):
        if index % 128 == 0:
            check_cancel(cancel)
        back = tuple(sorted(fixed + rest))
        logs = [pair_logs.get(pair) for pair in combinations(back, 2)]
        if any(weight is None for weight in logs):
            continue
        backs.append(back)
        # 多个指标在单个对子内已经相乘；复式再把对子分数按同一尺度合并。
        logs_by_back.append(sum(logs) / len(logs))
    check_cancel(cancel)
    if not backs:
        raise ValueError("后区固定/排除号码或结构权重限制过严，没有可用的后区组合")
    return BackStructurePool(tuple(backs), tuple(logs_by_back), relative_cumulative(logs_by_back))

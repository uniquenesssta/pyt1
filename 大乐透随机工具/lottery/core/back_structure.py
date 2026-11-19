"""后区单式和复式的有限候选；复用每个 2 码对子的结构评分。"""
from bisect import bisect_right
from dataclasses import dataclass
from itertools import combinations
from math import exp, log, prod

from .models import check_cancel
from .structure_scoring import StructureScorer
from .trend_indicators import BACK, BACK_INDICATORS


@dataclass(frozen=True)
class BackStructurePool:
    backs: tuple
    weights: tuple
    cumulative: tuple

    def choose(self, rng):
        index = bisect_right(self.cumulative, rng.random() * self.cumulative[-1])
        return self.backs[min(index, len(self.backs) - 1)]


def build_back_structure(pool, fixed, size, frequencies, profile, cancel=None):
    if profile is None or not any(profile.strengths[name] for name in BACK_INDICATORS):
        return None
    check_cancel(cancel)
    scorer = StructureScorer(profile, BACK)
    pair_logs = {}
    for pair in combinations(sorted(fixed + pool), 2):
        weight = scorer.weight(pair)
        if weight > 0:
            pair_logs[pair] = log(weight)

    scale = max((frequencies[n] for n in pool), default=1)
    backs, weights, cumulative = [], [], []
    total = 0.0
    for index, rest in enumerate(combinations(pool, size - len(fixed))):
        if index % 128 == 0:
            check_cancel(cancel)
        back = tuple(sorted(fixed + rest))
        logs = [pair_logs.get(pair) for pair in combinations(back, 2)]
        if any(weight is None for weight in logs):
            continue
        score = exp(sum(logs) / len(logs))
        weight = score * prod(frequencies[n] / scale for n in rest)
        total += weight
        backs.append(back)
        weights.append(weight)
        cumulative.append(total)
    check_cancel(cancel)
    if not backs:
        raise ValueError("后区固定/排除号码或结构权重限制过严，没有可用的后区组合")
    return BackStructurePool(tuple(backs), tuple(weights), tuple(cumulative))

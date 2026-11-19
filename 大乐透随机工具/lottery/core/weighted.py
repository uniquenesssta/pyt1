"""历史权重抽样；结构模式采用有限全集，避免旧版无限拒绝重试。"""
from bisect import bisect_right
from itertools import accumulate, combinations
from math import exp, log
from .features import features
from .models import check_cancel


def weighted_sample(pool, count, weights, rng):
    # 集合权重=各号码权重之积；动态规划直接抽样，支持接近全选的复式。
    scale = max((weights[n] for n in pool), default=1)
    values = [weights[n] / scale for n in pool]
    suffix = [[0.0] * (count + 1) for _ in range(len(pool) + 1)]
    suffix[-1][0] = 1.0
    for i in range(len(pool) - 1, -1, -1):
        suffix[i][0] = 1.0
        for k in range(1, count + 1):
            suffix[i][k] = suffix[i+1][k] + values[i] * suffix[i+1][k-1]
    result = []
    needed = count
    for i, number in enumerate(pool):
        if not needed:
            break
        probability = values[i] * suffix[i+1][needed-1] / suffix[i][needed]
        if rng.random() < probability:
            result.append(number)
            needed -= 1
    return result


class StructurePool:
    def __init__(self, config, cancel=None, progress=None):
        self.fronts, self.log_weights = [], []
        pool = [n for n in range(1, 36) if n not in config.front_fixed and n not in config.front_excluded]
        # 兼容直接传入跨区权重的入口；未指定的跨区指标也不参与。
        max_weights = config.max_span_weights or (1,) * 5
        start_weights = config.start_span_weights or (1,) * 5
        from .structure_scoring import StructureScorer
        scorer = (StructureScorer(config.structure_profile, config.indicators)
                  if config.structure_profile is not None else None)
        for i, rest in enumerate(combinations(pool, 5 - len(config.front_fixed))):
            if i % 1024 == 0:
                check_cancel(cancel)
                if progress:
                    progress(f"正在计算结构候选 {i:,} / 最多 324,632")
            front = tuple(sorted(config.front_fixed + rest))
            if scorer is not None:
                score = scorer.log_weight(front)
                if score is not None:
                    self.fronts.append(front)
                    self.log_weights.append(score)
                continue
            f = features(front)
            if max_weights[f.max_span] == 0 or start_weights[f.start_span] == 0:
                continue
            self.fronts.append(front)
            self.log_weights.append(log(max_weights[f.max_span]) + log(start_weights[f.start_span]))
        check_cancel(cancel)
        if not self.fronts:
            raise ValueError("固定/排除号码或结构权重限制过严，没有可用的前区组合")
        self.cumulative = relative_cumulative(self.log_weights)

    def choose(self, rng):
        index = bisect_right(self.cumulative, rng.random() * self.cumulative[-1])
        return self.fronts[min(index, len(self.fronts) - 1)]


def relative_cumulative(log_weights):
    highest = max(log_weights)
    return tuple(accumulate(exp(score - highest) for score in log_weights))

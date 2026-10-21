"""历史权重抽样；结构模式采用有限全集，避免旧版无限拒绝重试。"""
from bisect import bisect_right
from itertools import combinations
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
    def __init__(self, config, stats, cancel=None, progress=None):
        self.fronts, self.cumulative = [], []
        pool = [n for n in range(1, 36) if n not in config.front_fixed and n not in config.front_excluded]
        # 平滑各历史类别，避免小样本中未出现过的结构被永久禁止。
        max_weights = config.max_span_weights or tuple(stats.max_span[i] + 1 for i in range(5))
        start_weights = config.start_span_weights or tuple(stats.start_span[i] + 1 for i in range(5))
        total = 0.0
        for i, rest in enumerate(combinations(pool, 5 - len(config.front_fixed))):
            if i % 1024 == 0:
                check_cancel(cancel)
                if progress:
                    progress(f"正在计算结构候选 {i:,} / 最多 324,632")
            front = tuple(sorted(config.front_fixed + rest))
            f = features(front)
            if max_weights[f.max_span] == 0 or start_weights[f.start_span] == 0:
                continue
            # 各维度为相对权重而非承诺的最终边际概率。几何平均抑制重复放大。
            factors = [stats.front[n] + 1 for n in front]
            factors += [stats.gaps[j][gap] + 1 for j, gap in enumerate(f.gaps)]
            factors += [stats.runs[f.longest_run] + 1]
            factors += [(stats.empty[z] if z in f.empty_zones else stats.total - stats.empty[z]) + 1
                        for z in range(1, 6)]
            weight = exp(sum(log(v) for v in factors) / len(factors))
            weight *= max_weights[f.max_span] * start_weights[f.start_span]
            total += weight
            self.fronts.append(front)
            self.cumulative.append(total)
        check_cancel(cancel)
        if not self.fronts:
            raise ValueError("固定/排除号码与跨区权重冲突，没有可用的前区组合")

    def choose(self, rng):
        index = bisect_right(self.cumulative, rng.random() * self.cumulative[-1])
        return self.fronts[min(index, len(self.fronts) - 1)]

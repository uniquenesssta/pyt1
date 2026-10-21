"""小候选空间的精确无放回抽样，保持与集合乘积权重同一分布。"""
from heapq import nlargest
from math import log, prod
from .models import Ticket, check_cancel


def subset_probability(subset, pool, weights):
    """动态规划求乘积权重的归一化概率，复杂度 O(号码池×选号数)。"""
    scale = max((weights[n] for n in pool), default=1)
    sums = [1.0] + [0.0] * len(subset)
    for n in pool:
        for k in range(len(subset), 0, -1):
            sums[k] += weights[n] / scale * sums[k-1]
    return prod(weights[n] / scale for n in subset) / sums[-1]


def select_small_space(fronts, backs, config, fw, bw, structure, rng, cancel):
    fp = [n for n in range(1, 36) if n not in config.front_fixed and n not in config.front_excluded]
    bp = [n for n in range(1, 13) if n not in config.back_fixed and n not in config.back_excluded]
    fweights = []
    for i, front in enumerate(fronts):
        check_cancel(cancel)
        if structure:
            value = structure.cumulative[i] - (structure.cumulative[i-1] if i else 0)
        else:
            value = subset_probability(tuple(n for n in front if n not in config.front_fixed), fp, fw)
        fweights.append(value)
    bweights = [subset_probability(tuple(n for n in back if n not in config.back_fixed), bp, bw) for back in backs]

    def candidates():
        index = 0
        for f, front in enumerate(fronts):
            for b, back in enumerate(backs):
                if index % 100 == 0:
                    check_cancel(cancel)
                key = log(1.0 - rng.random()) / (fweights[f] * bweights[b])
                yield key, index, Ticket(front, back)
                index += 1

    result = [ticket for _, _, ticket in nlargest(config.count, candidates())]
    check_cancel(cancel)
    return result

"""无固定、排除时的均匀组合基准及新增指标的建议权重。"""
from collections import Counter
from functools import lru_cache
from itertools import combinations
from math import comb, prod

from .trend_indicators import TREND_INDICATORS, ZONE_SIZES, ac_value


def _sum_counts(maximum, size):
    distributions = [Counter({0: 1})] + [Counter() for _ in range(size)]
    for n in range(1, maximum + 1):
        for k in range(min(size, n), 0, -1):
            distributions[k].update({total + n: count for total, count in distributions[k - 1].items()})
    return distributions[size]


def ratio_counts(categories, population):
    return {key: prod(comb(available, int(taken)) for available, taken in zip(population, key.split(":")))
            for key in categories}


def _tail_counts(maximum, size):
    states = Counter({(0, 0): 1})
    for tail in range(10):
        available = sum(n % 10 == tail for n in range(1, maximum + 1))
        updated = Counter()
        for (chosen, groups), count in states.items():
            for k in range(min(available, size - chosen) + 1):
                updated[chosen+k, groups+int(k >= 2)] += count * comb(available, k)
        states = updated
    return {groups: states[size, groups] for groups in range(size//2 + 1)}


def _ac_counts(maximum, size):
    # 先枚举以 0 开始的相对位置，每种形态再平移到合法号码区间。
    counts = Counter()
    for rest in combinations(range(1, maximum), size - 1):
        counts[ac_value((0,) + rest)] += maximum - rest[-1]
    return counts


@lru_cache(maxsize=len(TREND_INDICATORS))
def uniform_fractions(name):
    indicator = TREND_INDICATORS[name]
    maximum, size = ZONE_SIZES[indicator.zone]
    if indicator.kind == "和值":
        counts = _sum_counts(maximum, size)
    elif indicator.kind == "跨度":
        counts = {gap: (maximum - gap) * comb(gap - 1, size - 2) for gap in indicator.categories}
    elif indicator.kind == "同尾组数":
        counts = _tail_counts(maximum, size)
    elif indicator.kind == "AC值":
        counts = _ac_counts(maximum, size)
    elif indicator.position:
        i = indicator.position
        counts = {v: comb(v-1, i-1) * comb(maximum-v, size-i) for v in indicator.categories}
    else:
        counts = ratio_counts(indicator.categories, indicator.population)
    total = comb(maximum, size)
    return {key: counts[key] / total for key in indicator.categories}


def calibrated_weights(counts, samples, fractions):
    """频数贴近均匀基准时给 50；平滑小样本并限制放大幅度。"""
    return {key: 50 * min(2.0, max(0.5, (counts[key] + 5) / (samples * fraction + 5)))
            for key, fraction in fractions.items()}


def trend_suggestions(name, counts, samples):
    return calibrated_weights(counts, samples, uniform_fractions(name))

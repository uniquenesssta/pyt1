"""无固定、排除时的均匀组合基准及新增指标的建议权重。"""
from collections import Counter
from functools import lru_cache
from math import comb, prod

from .trend_indicators import TREND_INDICATORS, ZONE_SIZES


def _sum_counts(maximum, size):
    distributions = [Counter({0: 1})] + [Counter() for _ in range(size)]
    for n in range(1, maximum + 1):
        for k in range(min(size, n), 0, -1):
            distributions[k].update({total + n: count for total, count in distributions[k - 1].items()})
    return distributions[size]


def _ratio_counts(indicator, maximum):
    if indicator.kind == "奇偶比":
        sizes = ((maximum + 1) // 2, maximum // 2)
    elif indicator.kind == "小大比":
        sizes = (maximum // 2, (maximum + 1) // 2)
    else:
        sizes = tuple(sum(n % 3 == remainder for n in range(1, maximum + 1)) for remainder in range(3))
    return {key: prod(comb(available, int(taken)) for available, taken in zip(sizes, key.split(":")))
            for key in indicator.categories}


@lru_cache(maxsize=len(TREND_INDICATORS))
def uniform_fractions(name):
    indicator = TREND_INDICATORS[name]
    maximum, size = ZONE_SIZES[indicator.zone]
    if indicator.kind == "和值":
        counts = _sum_counts(maximum, size)
    elif indicator.kind == "跨度":
        counts = {gap: (maximum - gap) * comb(gap - 1, size - 2) for gap in indicator.categories}
    else:
        counts = _ratio_counts(indicator, maximum)
    total = comb(maximum, size)
    return {key: counts[key] / total for key in indicator.categories}


def trend_suggestions(name, counts, samples):
    """频数贴近均匀基准时给 50；平滑小样本并限制放大幅度。"""
    return {key: 50 * min(2.0, max(0.5, (counts[key] + 5) / (samples * fraction + 5)))
            for key, fraction in uniform_fractions(name).items()}

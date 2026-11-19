"""走势图常见的单期指标；前、后区分别按 5、2 个开奖号计算。"""
from dataclasses import dataclass
from itertools import product
from typing import Callable


FRONT, BACK = "前区", "后区"
ZONE_SIZES = {FRONT: (35, 5), BACK: (12, 2)}


@dataclass(frozen=True)
class TrendIndicator:
    zone: str
    kind: str
    categories: tuple
    value: Callable
    description: str
    parts: tuple = ()


def split_ratio(count, size):
    return f"{count}:{size - count}"


def odd_even(numbers):
    return split_ratio(sum(n % 2 for n in numbers), len(numbers))


def small_large(numbers, boundary):
    return split_ratio(sum(n <= boundary for n in numbers), len(numbers))


def modulo_three(numbers):
    counts = [0, 0, 0]
    for n in numbers:
        counts[n % 3] += 1
    return ":".join(map(str, counts))


def span(numbers):
    return max(numbers) - min(numbers)


def _zone_indicators(zone, maximum, size):
    boundary = maximum // 2
    splits = tuple(split_ratio(n, size) for n in range(size + 1))
    residues = tuple(":".join(map(str, parts)) for parts in product(range(size + 1), repeat=3)
                     if sum(parts) == size)
    min_sum = size * (size + 1) // 2
    max_sum = sum(range(maximum - size + 1, maximum + 1))
    return (
        TrendIndicator(zone, "奇偶比", splits, odd_even, "奇数个数:偶数个数", ("奇", "偶")),
        TrendIndicator(zone, "小大比", splits, lambda ns: small_large(ns, boundary),
                       f"小号个数:大号个数；01–{boundary:02d} 为小，{boundary+1:02d}–{maximum} 为大",
                       ("小", "大")),
        TrendIndicator(zone, "012路比", residues, modulo_three, "除以 3 后余 0、1、2 的号码个数",
                       ("0路", "1路", "2路")),
        TrendIndicator(zone, "和值", tuple(range(min_sum, max_sum + 1)), sum, "该区开奖号之和"),
        TrendIndicator(zone, "跨度", tuple(range(size - 1, maximum)), span,
                       "该区最大号减最小号；前区跨度等于 C1–C4 差值之和"),
    )


TREND_INDICATORS = {item.zone + item.kind: item for zone, (maximum, size) in ZONE_SIZES.items()
                    for item in _zone_indicators(zone, maximum, size)}
BACK_INDICATORS = frozenset(name for name, item in TREND_INDICATORS.items() if item.zone == BACK)


def trend_values(numbers, zone):
    return {name: indicator.value(numbers) for name, indicator in TREND_INDICATORS.items()
            if indicator.zone == zone}

"""走势图常见的单期指标；前、后区分别按 5、2 个开奖号计算。"""
from dataclasses import dataclass
from itertools import accumulate, combinations, product
from typing import Callable


FRONT, BACK = "前区", "后区"
ZONE_SIZES = {FRONT: (35, 5), BACK: (12, 2)}
PRIMES = frozenset((2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31))


@dataclass(frozen=True)
class TrendIndicator:
    zone: str
    kind: str
    categories: tuple
    value: Callable
    description: str
    parts: tuple = ()
    population: tuple = ()
    position: int = 0


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


def ratio_categories(size, population):
    return tuple(":".join(map(str, counts))
                 for counts in product(*(range(min(size, count) + 1) for count in population))
                 if sum(counts) == size)


def same_tail_groups(numbers):
    seen, repeats = 0, 0
    for number in numbers:
        tail = 1 << (number % 10)
        repeats |= seen & tail
        seen |= tail
    return repeats.bit_count()


def ac_value(numbers):
    return len({abs(b - a) for a, b in combinations(numbers, 2)}) - (len(numbers) - 1)


def _number_ratio(zone, kind, maximum, size, membership, parts, description):
    codes = (None,) + tuple(membership(n) for n in range(1, maximum + 1))
    population = tuple(codes.count(i) for i in range(len(parts)))

    def value(numbers):
        counts = [0] * len(parts)
        for n in numbers:
            counts[codes[n]] += 1
        return ":".join(map(str, counts))

    return TrendIndicator(zone, kind, ratio_categories(size, population), value,
                          description, parts, population)


def _region_ratio(zone, maximum, size, population):
    bounds = tuple(accumulate(population))
    ranges = " / ".join(f"{start+1:02d}–{end:02d}" for start, end in zip((0,) + bounds, bounds))
    title = "三区比" if len(population) == 3 else "五区比"
    return _number_ratio(zone, title, maximum, size,
                         lambda n: next(i for i, end in enumerate(bounds) if n <= end),
                         tuple(f"{i+1}区" for i in range(len(population))),
                         f"按从小到大的分区统计每区个数：{ranges}")


def _zone_indicators(zone, maximum, size):
    boundary = maximum // 2
    splits = tuple(split_ratio(n, size) for n in range(size + 1))
    residues = tuple(":".join(map(str, parts)) for parts in product(range(size + 1), repeat=3)
                     if sum(parts) == size)
    min_sum = size * (size + 1) // 2
    max_sum = sum(range(maximum - size + 1, maximum + 1))
    metrics = (
        TrendIndicator(zone, "奇偶比", splits, odd_even, "奇数个数:偶数个数", ("奇", "偶"),
                       ((maximum + 1) // 2, boundary)),
        TrendIndicator(zone, "小大比", splits, lambda ns: small_large(ns, boundary),
                       f"小号个数:大号个数；01–{boundary:02d} 为小，{boundary+1:02d}–{maximum} 为大",
                       ("小", "大"), (boundary, maximum - boundary)),
        TrendIndicator(zone, "012路比", residues, modulo_three, "除以 3 后余 0、1、2 的号码个数",
                       ("0路", "1路", "2路"),
                       tuple(sum(n % 3 == r for n in range(1, maximum + 1)) for r in range(3))),
        TrendIndicator(zone, "和值", tuple(range(min_sum, max_sum + 1)), sum, "该区开奖号之和"),
        TrendIndicator(zone, "跨度", tuple(range(size - 1, maximum)), span,
                       "该区最大号减最小号；前区跨度等于 C1–C4 差值之和"),
        TrendIndicator(zone, "同尾组数", tuple(range(size // 2 + 1)), same_tail_groups,
                       "个位相同且至少两号的一组计 1；01、11、21 合计 1 组"),
        _number_ratio(zone, "质合比", maximum, size, lambda n: 2 if n == 1 else 0 if n in PRIMES else 1,
                      ("质", "合", "号码01"), "质数个数:合数个数:号码01个数；1 既非质数也非合数"),
        _region_ratio(zone, maximum, size, (12, 12, 11) if zone == FRONT else (4, 4, 4)),
    )
    if zone == FRONT:
        metrics += (
            _region_ratio(zone, maximum, size, (7,) * 5),
            TrendIndicator(zone, "AC值", tuple(range(7)), ac_value, "所有两两正差去重后的个数减 4"),
        )
    return metrics + tuple(
        TrendIndicator(zone, f"第{position}位", tuple(range(position, maximum - size + position + 1)),
                       lambda ns, idx=position-1: ns[idx],
                       f"该区号码升序排列后的第 {position} 位，不是摇出顺序", position=position)
        for position in range(1, size + 1)
    )


TREND_INDICATORS = {item.zone + item.kind: item for zone, (maximum, size) in ZONE_SIZES.items()
                    for item in _zone_indicators(zone, maximum, size)}
def trend_values(numbers, zone):
    return {name: indicator.value(numbers) for name, indicator in TREND_INDICATORS.items()
            if indicator.zone == zone}

"""按上一期及连续遗漏生成重邻孤、遗漏结构和对应理论基准。"""
from dataclasses import dataclass
from functools import lru_cache
from math import comb

from .trend_baseline import ratio_counts
from .trend_indicators import ZONE_SIZES, ratio_categories


@dataclass(frozen=True)
class TemporalIndicator:
    zone: str
    categories: tuple
    description: str
    relation_index: int | None = None
    parts: tuple = ()

    def codes(self, reference):
        if reference is None:
            return None
        zone = reference.zone(self.zone)
        return zone.omission if self.parts else zone.relation

    def value(self, numbers, reference):
        codes = self.codes(reference)
        if codes is None:
            return None
        if self.parts:
            counts = [0] * len(self.parts)
            for number in numbers:
                counts[codes[number]] += 1
            return ":".join(map(str, counts))
        return sum(codes[n] == self.relation_index for n in numbers)


def _metrics():
    for zone, (_, size) in ZONE_SIZES.items():
        for index, (name, description) in enumerate((
            ("重号数", "该区与紧邻上一期相同的号码个数"),
            ("邻号数", "与该区上一期某号码相差 1，且本身不属于重号"),
            ("孤号数", "既非重号、也非邻号的号码个数"),
        )):
            yield zone + name, TemporalIndicator(zone, tuple(range(size + 1)), description, index)
        yield zone + "遗漏结构", TemporalIndicator(
            zone, ratio_categories(size, (size,) * 4),
            "按开奖前连续未出的期数分四档，至少需要连续 12 期参照",
            parts=("0期", "1–5期", "6–11期", "12期以上"),
        )


TEMPORAL_INDICATORS = dict(_metrics())


@lru_cache(maxsize=1024)
def temporal_fractions(name, population):
    indicator = TEMPORAL_INDICATORS[name]
    maximum, size = ZONE_SIZES[indicator.zone]
    total = comb(maximum, size)
    if indicator.parts:
        counts = ratio_counts(indicator.categories, population)
    else:
        available = population[indicator.relation_index]
        counts = {k: comb(available, k) * comb(maximum - available, size - k) for k in indicator.categories}
    return {key: value / total for key, value in counts.items()}

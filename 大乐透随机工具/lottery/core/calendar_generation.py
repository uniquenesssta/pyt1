"""用同期样本的四项结构抽单注，再按组合权重扩成两档复式。"""
from collections import Counter
from itertools import combinations
from math import comb, prod
from random import SystemRandom

from .models import Ticket, check_cancel
from .trend_baseline import trend_suggestions
from .trend_indicators import TREND_INDICATORS
from .weighted import weighted_sample


FRONT_METRICS = ("前区第1位", "前区第5位", "前区奇偶比")
BACK_METRICS = ("后区跨度",)


def calendar_factors(samples, front):
    factors = []
    for name in FRONT_METRICS if front else BACK_METRICS:
        value = TREND_INDICATORS[name].value
        counts = Counter(value(draw.ticket.front if front else draw.ticket.back) for draw in samples.draws)
        factors.append((value, trend_suggestions(name, counts, len(samples.draws))))
    return tuple(factors)


def _nested_zone(maximum, fixed, excluded, sizes, factors, rng, cancel, progress, area):
    pool = tuple(n for n in range(1, maximum+1) if n not in fixed and n not in excluded)
    needed = sizes[0] - len(fixed)
    candidates = comb(len(pool), needed)
    totals = {n: 0.0 for n in pool}
    picked, total = None, 0.0
    for i, choices in enumerate(combinations(pool, needed)):
        if i % 1024 == 0:
            check_cancel(cancel)
            if progress:
                progress(f"正在计算同期{area}结构 {i:,}/{candidates:,}")
        numbers = tuple(sorted(fixed + choices)) if fixed else choices
        weight = prod(weights[value(numbers)] / 50 for value, weights in factors)
        total += weight
        # 加权蓄水池只保留本次 1 个候选，无需存下全部 324,632 个组合。
        if rng.random() * total < weight:
            picked = numbers
        for n in choices:
            totals[n] += weight
    check_cancel(cancel)
    if picked is None:
        raise ValueError(f"{area}没有可用的基础号码组合")

    # 全部基础号码被固定时，扩充的号码没有可比边际，按合法范围等权。
    marginal = totals if needed else dict.fromkeys(pool, 1)
    nested = [picked]
    for size in sizes[1:]:
        remaining = tuple(n for n in pool if n not in picked)
        extra = weighted_sample(remaining, size - len(picked), marginal, rng)
        picked = tuple(sorted(picked + tuple(extra)))
        nested.append(picked)
    return tuple(nested)


def generate_calendar_set(config, samples, cancel=None, progress=None, rng=None):
    config.validate()
    if (config.count, config.front_count, config.back_count) != (1, 5, 2):
        raise ValueError("同星期／历年同期每次按一套 5+2 基础号码生成三档")
    for available, required, area in ((35 - len(config.front_excluded), 15, "前区"),
                                      (12 - len(config.back_excluded), 5, "后区")):
        if available < required:
            raise ValueError(f"{area}排除后不足 {required} 个号码，无法生成 15+5")
    if not samples.draws:
        raise ValueError("没有可用的同期历史样本")
    check_cancel(cancel)
    rng = rng if rng is not None else SystemRandom()
    fronts = _nested_zone(35, config.front_fixed, config.front_excluded, (5, 9, 15),
                          calendar_factors(samples, True), rng, cancel, progress, "前区")
    backs = _nested_zone(12, config.back_fixed, config.back_excluded, (2, 3, 5),
                         calendar_factors(samples, False), rng, cancel, progress, "后区")
    check_cancel(cancel)
    return tuple(Ticket(front, back) for front, back in reversed(tuple(zip(fronts, backs))))

"""细分结构的历史分布、均值与可编辑权重。"""
from collections import Counter
from dataclasses import dataclass
from math import isfinite
from .features import features
from .history_window import select_window
from .statistics import analyze
from .trend_baseline import trend_suggestions
from .trend_indicators import BACK, FRONT, TREND_INDICATORS, trend_values


def classic_values(front, f=None):
    f = features(front) if f is None else f
    runs, size = [], 1
    for gap in f.gaps:
        if gap == 1:
            size += 1
        else:
            runs.append(size); size = 1
    runs.append(size)
    values = {f'C{i+1}差值': gap for i, gap in enumerate(f.gaps)}
    values.update({'最长连号': f.longest_run,
                   '连号形态': '+'.join(map(str, sorted(runs, reverse=True))),
                   '空区数量': len(f.empty_zones),
                   '最大跨区（差值>7）': f.max_span, '起始跨区': f.start_span})
    for z in range(1, 6):
        values[f'{z}区空区'] = int(z in f.empty_zones)
        values[f'{z}区中间覆盖（差值>10）'] = int(z in f.intermediate_zones)
    return values


def structure_values(front, back=()):
    values = classic_values(front)
    values.update(trend_values(front, FRONT))
    if back:
        values.update(trend_values(back, BACK))
    return values


def domains():
    values = {f'C{i}差值': tuple(range(1, 32)) for i in range(1, 5)}
    values.update({'最长连号': tuple(range(1, 6)),
                   '连号形态': ('1+1+1+1+1','2+1+1+1','2+2+1','3+1+1','3+2','4+1','5'),
                   '空区数量': tuple(range(5)),
                   '最大跨区（差值>7）': tuple(range(5)), '起始跨区': tuple(range(5))})
    for z in range(1, 6):
        values[f'{z}区空区'] = (0,1)
        values[f'{z}区中间覆盖（差值>10）'] = (0,1)
    values.update({name: indicator.categories for name, indicator in TREND_INDICATORS.items()})
    return values


def _suggestions(name, keys, counts, samples):
    if name in TREND_INDICATORS:
        return trend_suggestions(name, counts, samples)
    return {key: 100 * (counts[key]+1)/(samples+len(keys)) for key in keys}


def _average(name, keys, counts, samples):
    if isinstance(keys[0], int):
        return sum(key * counts[key] for key in keys) / samples
    indicator = TREND_INDICATORS.get(name)
    if indicator and indicator.parts:
        totals = [0] * len(indicator.parts)
        for key, count in counts.items():
            for i, value in enumerate(key.split(":")):
                totals[i] += int(value) * count
        return tuple(total / samples for total in totals)
    return None


@dataclass
class StructureProfile:
    draws: list
    order: str
    requested: int
    stats: object
    counts: dict
    weights: dict
    strengths: dict
    means: dict

    def suggested_weights(self, name):
        return _suggestions(name, domains()[name], self.counts[name], len(self.draws))

    def validate(self):
        for name, categories in domains().items():
            strength = self.strengths[name]
            if not isfinite(strength) or not 0 <= strength <= 10:
                raise ValueError('指标强度须为 0–10；0 表示不参与')
            weights = [self.weights[name][k] for k in categories]
            if any(not isfinite(w) or not 0 <= w <= 100 for w in weights):
                raise ValueError('类别权重须为 0–100 的有限数值')
            if strength and not any(weights):
                raise ValueError(f'{name}不能全部为 0，或将指标强度设为 0')


def build_profile(draws, periods=50):
    selected, order = select_window(draws, periods)
    categories = domains()
    counters = {name: Counter() for name in categories}
    for draw in selected:
        for name, value in structure_values(draw.ticket.front, draw.ticket.back).items():
            counters[name][value] += 1
    weights, means = {}, {}
    for name, keys in categories.items():
        counts = counters[name]
        weights[name] = _suggestions(name, keys, counts, len(selected))
        average = _average(name, keys, counts, len(selected))
        if average is not None:
            means[name] = average
    strengths = {name: 0.0 if name in TREND_INDICATORS else 1.0 for name in counters}
    # 形态已包含最长连号；空区数量与各区空区相关，默认避免重复叠加强调。
    strengths['最长连号'] = 0.0
    strengths['空区数量'] = 0.0
    return StructureProfile(selected, order, periods, analyze(selected), counters, weights, strengths, means)

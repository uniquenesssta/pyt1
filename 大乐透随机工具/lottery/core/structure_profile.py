"""细分结构的历史分布、均值与可编辑权重。"""
from collections import Counter
from dataclasses import dataclass
from math import isfinite
from .features import features
from .period_context import PeriodReference, scoped_references
from .statistics import analyze
from .temporal_indicators import TEMPORAL_INDICATORS, temporal_fractions
from .trend_baseline import calibrated_weights, uniform_fractions
from .trend_indicators import BACK, FRONT, TREND_INDICATORS, trend_values


INDICATORS = {**TREND_INDICATORS, **TEMPORAL_INDICATORS}


def indicator_zone(name):
    indicator = INDICATORS.get(name)
    return indicator.zone if indicator else FRONT


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


def indicator_value(name, draw, reference=None):
    indicator = INDICATORS.get(name)
    if indicator is None:
        values = classic_values(draw.ticket.front)
        if name not in values:
            raise ValueError('未知结构指标')
        return values[name]
    numbers = draw.ticket.front if indicator.zone == FRONT else draw.ticket.back
    return indicator.value(numbers, reference) if name in TEMPORAL_INDICATORS else indicator.value(numbers)


def domains():
    values = {f'C{i}差值': tuple(range(1, 32)) for i in range(1, 5)}
    values.update({'最长连号': tuple(range(1, 6)),
                   '连号形态': ('1+1+1+1+1','2+1+1+1','2+2+1','3+1+1','3+2','4+1','5'),
                   '空区数量': tuple(range(5)),
                   '最大跨区（差值>7）': tuple(range(5)), '起始跨区': tuple(range(5))})
    for z in range(1, 6):
        values[f'{z}区空区'] = (0,1)
        values[f'{z}区中间覆盖（差值>10）'] = (0,1)
    values.update({name: indicator.categories for name, indicator in INDICATORS.items()})
    return values


def _suggestions(keys, counts, samples, fractions):
    if not samples:
        return dict.fromkeys(keys, 50.0)
    if fractions is not None:
        return calibrated_weights(counts, samples, fractions)
    return {key: 100 * (counts[key]+1)/(samples+len(keys)) for key in keys}


def _average(name, keys, counts, samples):
    if not samples:
        return None
    if isinstance(keys[0], int):
        return sum(key * counts[key] for key in keys) / samples
    indicator = INDICATORS.get(name)
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
    temporal_samples: dict
    temporal_baselines: dict
    reference: PeriodReference | None

    def samples(self, name):
        return self.temporal_samples.get(name, len(self.draws))

    def baseline(self, name):
        return uniform_fractions(name) if name in TREND_INDICATORS else self.temporal_baselines.get(name)

    def suggested_weights(self, name):
        return _suggestions(domains()[name], self.counts[name], self.samples(name), self.baseline(name))

    def validate(self, selected=()):
        if len(set(selected)) != len(selected):
            raise ValueError('加权指标不能重复选择')
        for name in selected:
            if name not in self.weights:
                raise ValueError(f'未知加权指标：{name}')
        for name, categories in domains().items():
            strength = self.strengths[name]
            if not isfinite(strength) or not 0 <= strength <= 10:
                raise ValueError('指标强度须为 0–10；0 表示不参与')
            weights = [self.weights[name][k] for k in categories]
            if any(not isfinite(w) or not 0 <= w <= 100 for w in weights):
                raise ValueError('类别权重须为 0–100 的有限数值')
            if name not in selected:
                continue
            if strength == 0:
                raise ValueError(f'{name}已选，但强度为 0；请设为正数或移除该指标')
            if not any(weights):
                raise ValueError(f'{name}已选，但所有类别权重为 0')
            if name in TEMPORAL_INDICATORS:
                indicator = TEMPORAL_INDICATORS[name]
                if not self.samples(name) or indicator.codes(self.reference) is None:
                    raise ValueError(f'{name}没有足够的连续期开奖；请补齐数据或移除该指标')


def build_profile(draws, periods=50):
    selected, order, references, last = scoped_references(draws, periods)
    categories = domains()
    counters = {name: Counter() for name in categories}
    samples = dict.fromkeys(TEMPORAL_INDICATORS, 0)
    expected = {name: Counter() for name in TEMPORAL_INDICATORS}
    for draw in selected:
        for name, value in structure_values(draw.ticket.front, draw.ticket.back).items():
            counters[name][value] += 1
        reference = references.get(draw)
        if reference is not None:
            for name, indicator in TEMPORAL_INDICATORS.items():
                codes = indicator.codes(reference)
                if codes is None:
                    continue
                value = indicator_value(name, draw, reference)
                counters[name][value] += 1
                samples[name] += 1
                population = tuple(codes.count(i) for i in range(len(indicator.parts) or 3))
                expected[name].update(temporal_fractions(name, population))
    baselines = {name: {key: v/samples[name] for key, v in values.items()}
                 for name, values in expected.items() if samples[name]}
    means = {}
    for name, keys in categories.items():
        average = _average(name, keys, counters[name], samples.get(name, len(selected)))
        if average is not None:
            means[name] = average
    # 强度只是已选指标的倍率；未显式选择的任何指标都不参与。
    profile = StructureProfile(selected, order, periods, analyze(selected), counters, {},
                               dict.fromkeys(counters, 1.0), means, samples, baselines, last)
    profile.weights = {name: profile.suggested_weights(name) for name in categories}
    return profile

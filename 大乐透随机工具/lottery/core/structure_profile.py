"""细分结构的历史分布、均值与可编辑权重。"""
from collections import Counter
from dataclasses import dataclass
from math import isfinite
from .features import features
from .history_window import select_window
from .statistics import analyze


def structure_values(front):
    f = features(front)
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


def domains():
    values = {f'C{i}差值': tuple(range(1, 32)) for i in range(1, 5)}
    values.update({'最长连号': tuple(range(1, 6)),
                   '连号形态': ('1+1+1+1+1','2+1+1+1','2+2+1','3+1+1','3+2','4+1','5'),
                   '空区数量': tuple(range(5)),
                   '最大跨区（差值>7）': tuple(range(5)), '起始跨区': tuple(range(5))})
    for z in range(1, 6):
        values[f'{z}区空区'] = (0,1)
        values[f'{z}区中间覆盖（差值>10）'] = (0,1)
    return values


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
    counters = {name: Counter() for name in domains()}
    for draw in selected:
        for name, value in structure_values(draw.ticket.front).items():
            counters[name][value] += 1
    weights, means = {}, {}
    for name, categories in domains().items():
        counts = counters[name]
        weights[name] = {key: 100 * (counts[key]+1)/(len(selected)+len(categories)) for key in categories}
        if all(type(k) is int for k in categories):
            means[name] = sum(k * counts[k] for k in categories)/len(selected)
    strengths = {name: 1.0 for name in counters}
    # 形态已包含最长连号；空区数量与各区空区相关，默认避免重复叠加强调。
    strengths['最长连号'] = 0.0
    strengths['空区数量'] = 0.0
    return StructureProfile(selected, order, periods, analyze(selected), counters, weights, strengths, means)

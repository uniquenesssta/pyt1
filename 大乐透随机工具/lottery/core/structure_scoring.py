"""只为显式选择的指标计分；多选按带强度的权重乘积计算。"""
from functools import partial
from math import exp, log
from .structure_profile import INDICATORS, classic_values, indicator_zone
from .temporal_indicators import TEMPORAL_INDICATORS
from .trend_indicators import FRONT


class StructureScorer:
    def __init__(self, profile, selected, zone=FRONT):
        profile.validate(selected)
        self.groups = []
        for name in sorted(selected):
            if indicator_zone(name) != zone:
                continue
            indicator = INDICATORS.get(name)
            value = indicator.value if indicator else None
            if name in TEMPORAL_INDICATORS:
                value = partial(value, reference=profile.reference)
            strength = profile.strengths[name]
            weights = profile.weights[name]
            log_scale = log(max(weights.values()))
            self.groups.append((name, value,
                                {key: strength * (log(weight) - log_scale) if weight else None
                                 for key, weight in weights.items()}))
        self.uses_classic = any(value is None for _, value, _ in self.groups)

    def log_weight(self, numbers, front_features=None):
        classic = classic_values(numbers, front_features) if self.uses_classic else None
        score = 0.0
        for name, value, logarithms in self.groups:
            weight = logarithms[classic[name] if value is None else value(numbers)]
            if weight is None:
                return None
            score += weight
        return score

    def weight(self, numbers):
        score = self.log_weight(numbers)
        return 0.0 if score is None else exp(score)

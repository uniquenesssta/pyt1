"""各结构指标独立配置后按强度组合；0 类别权重是硬排除。"""
from math import exp, log
from .structure_profile import classic_values
from .trend_indicators import FRONT, TREND_INDICATORS


class StructureScorer:
    def __init__(self, profile, zone=FRONT):
        profile.validate()
        self.groups = []
        self.total_strength = 0.0
        for name, strength in profile.strengths.items():
            indicator = TREND_INDICATORS.get(name)
            if not strength or (indicator.zone if indicator else FRONT) != zone:
                continue
            weights = profile.weights[name]
            log_total = log(sum(weights.values()))
            self.groups.append((name, indicator.value if indicator else None,
                                {key: strength * (log(weight) - log_total) if weight else None
                                 for key, weight in weights.items()}))
            self.total_strength += strength
        self.uses_classic = any(value is None for _, value, _ in self.groups)

    def weight(self, numbers, front_features=None):
        if not self.groups:
            return 1.0
        classic = classic_values(numbers, front_features) if self.uses_classic else None
        score = 0.0
        for name, value, logarithms in self.groups:
            weight = logarithms[classic[name] if value is None else value(numbers)]
            if weight is None:
                return 0.0
            score += weight
        return exp(score / self.total_strength)

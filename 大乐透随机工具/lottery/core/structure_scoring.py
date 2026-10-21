"""各结构指标独立配置后按强度组合；0 类别权重是硬排除。"""
from math import exp, log
from .structure_profile import structure_values


class StructureScorer:
    def __init__(self, profile):
        profile.validate()
        self.groups = []
        for name, strength in profile.strengths.items():
            if strength:
                total = sum(profile.weights[name].values())
                self.groups.append((name, strength, {k: v/total for k,v in profile.weights[name].items()}))
        self.total_strength = sum(s for _,s,_ in self.groups)

    def weight(self, front):
        if not self.groups:
            return 1.0
        values = structure_values(front)
        score = 0.0
        for name, strength, weights in self.groups:
            value = weights[values[name]]
            if value == 0:
                return 0.0
            score += strength * log(value)
        return exp(score/self.total_strength)

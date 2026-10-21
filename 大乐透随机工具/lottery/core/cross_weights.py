"""两页共享的跨区权重转换；覆盖同一指标，不重复相乘。"""
from copy import deepcopy
from dataclasses import replace

CROSS_GROUPS = ('最大跨区（差值>7）', '起始跨区')


def cross_values(profile):
    return tuple(tuple(profile.weights[name][i] for i in range(5)) for name in CROSS_GROUPS)


def with_cross_values(profile, values):
    updated = deepcopy(profile)
    for name, weights in zip(CROSS_GROUPS, values):
        if len(weights) != 5:
            raise ValueError('跨区权重须有0–4共五类')
        updated.weights[name] = dict(enumerate(weights))
    updated.validate()
    return updated


def resolve_cross_overrides(config):
    if config.structure_profile is None or not (config.max_span_weights or config.start_span_weights):
        return config
    previous = cross_values(config.structure_profile)
    profile = with_cross_values(config.structure_profile,
                                (config.max_span_weights or previous[0], config.start_span_weights or previous[1]))
    return replace(config, structure_profile=profile, max_span_weights=(), start_span_weights=())

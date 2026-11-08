"""Compose primary instructions and related auxiliary details without dropping choices."""
from scene_tool.config.close_auxiliary import GROUPS, KEYS
from scene_tool.config.close_dimensions import normalize_value
from scene_tool.config import highlight_position as position, surface_reflection as reflection


def close_lines(dimensions, values, hidden):
    primary, auxiliary = [], {}
    for key,label,canonical in dimensions:
        if key in hidden: continue
        value=normalize_value(canonical,values[key])
        if canonical==reflection.KEY: value=reflection.prompt_value(value)
        elif canonical==position.KEY: value=position.prompt_value(value)
        line=f'{label}：{value}'
        if canonical in KEYS: auxiliary[canonical]=line
        else: primary.append(line)
    for _,keys in GROUPS:
        lines=[auxiliary[k] for k in keys if k in auxiliary]
        if lines: primary.append('；'.join(lines))
    return primary

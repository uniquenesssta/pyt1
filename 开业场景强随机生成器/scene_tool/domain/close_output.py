"""Compose primary instructions and related auxiliary details without dropping choices."""
from scene_tool.config.close_auxiliary import GROUPS, KEYS
from scene_tool.config.appearance_rules import covered
from scene_tool.config.material_finish import effective
from scene_tool.domain.material_finish import validate
from scene_tool.config.close_dimensions import normalize_value
from scene_tool.config import highlight_position as position, surface_reflection as reflection


def close_lines(dimensions, values, hidden):
    dimensions=list(dimensions)
    light_key=next((k for k,_,c in dimensions if c==position.KEY),position.KEY)
    validate(values,hidden,light_key)
    primary, auxiliary = [], {}
    for key,label,canonical in dimensions:
        if key in hidden: continue
        value=normalize_value(canonical,values[key])
        if covered(canonical,value): continue
        if canonical==reflection.KEY: value=reflection.prompt_value(effective(values.get('close_finish'),value))
        elif canonical==position.KEY: value=position.prompt_value(value)
        line=f'{label}：{value}'
        if canonical in KEYS: auxiliary[canonical]=line
        else: primary.append(line)
    for _,keys in GROUPS:
        lines=[auxiliary[k] for k in keys if k in auxiliary]
        if lines: primary.append('；'.join(lines))
    return primary

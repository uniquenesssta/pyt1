from scene_tool.config.defaults import DIMENSIONS, DEFAULT_CONSTRAINTS
from scene_tool.domain.industry_profiles import dimensions
from scene_tool.config.render_styles import normalize_style
from scene_tool.config.photography import photo_requirements, DECORATION_REQUIREMENTS
from scene_tool.domain.copy_layout import copy_instructions
from scene_tool.domain.visibility import hidden_keys
from scene_tool.config.product_size import FIXED_LARGE
from scene_tool.domain.product_size import size_instructions, size_constraints, size_environment
from scene_tool.domain.render_style import styled_values, styled_constraints, styled_environment
from scene_tool.domain.environment import scene_parameters, environment_instructions, dimension_label

def make_prompt(values, industry='美业', constraints=DEFAULT_CONSTRAINTS,
                copy='盛大开业 · 美好启幕', extra='', hidden=None, render_style=None, product_size=FIXED_LARGE):
    render_style = normalize_style(render_style)
    active_dimensions = dimensions(render_style)
    hidden = hidden_keys(hidden)
    values = styled_values(values, render_style)
    values = dict(values)
    values.setdefault('environment', '室外')
    missing = [label for key, label in active_dimensions if key not in hidden and not values.get(key, '').strip()]
    if missing:
        raise ValueError('请填写：' + '、'.join(missing))
    lines = [photo_requirements(values.get("camera", ""), "camera" in hidden, render_style), DECORATION_REQUIREMENTS, '', size_constraints(styled_constraints(constraints, render_style), product_size).strip(), '',
             size_instructions(product_size), '', f'本轮行业：{industry.strip() or "通用"}', *(copy_instructions(copy) if 'copy' not in hidden else []), '',
             size_environment(styled_environment(environment_instructions(values), render_style), product_size) if 'environment' not in hidden else '', '', '本轮场景参数：']
    values = scene_parameters(values)
    lines.extend(f'{dimension_label(key, label, values)}：{values[key].strip()}' for key, label in active_dimensions if key not in hidden)
    if extra.strip():
        lines.extend(['', '补充要求：', extra.strip()])
    return '\n'.join(lines)


from scene_tool.config.defaults import DIMENSIONS, DEFAULT_CONSTRAINTS
from scene_tool.config.photography import PHOTO_REQUIREMENTS, DECORATION_REQUIREMENTS

def make_prompt(values, industry='美业', constraints=DEFAULT_CONSTRAINTS,
                copy='盛大开业 · 美好启幕', extra=''):
    missing = [label for key, label in DIMENSIONS if not values.get(key, '').strip()]
    if missing:
        raise ValueError('请填写：' + '、'.join(missing))
    lines = [PHOTO_REQUIREMENTS, DECORATION_REQUIREMENTS, '', constraints.strip(), '', f'本轮行业：{industry.strip() or "通用"}',
             f'开业文案：{copy.strip() or "盛大开业 · 美好启幕"}', '',
             '本轮场景参数：']
    lines.extend(f'{label}：{values[key].strip()}' for key, label in DIMENSIONS)
    if extra.strip():
        lines.extend(['', '补充要求：', extra.strip()])
    lines.extend(['', '结合随附参考图直接生成一张手机实拍风格照片。'])
    return '\n'.join(lines)

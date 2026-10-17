from scene_tool.config.defaults import DIMENSIONS, DEFAULT_CONSTRAINTS

def make_prompt(values, industry='美业', constraints=DEFAULT_CONSTRAINTS,
                copy='盛大开业 · 美好启幕', extra=''):
    missing = [label for key, label in DIMENSIONS if not values.get(key, '').strip()]
    if missing:
        raise ValueError('请填写：' + '、'.join(missing))
    lines = [constraints.strip(), '', f'本轮行业：{industry.strip() or "通用"}',
             f'开业文案：{copy.strip() or "盛大开业 · 美好启幕"}', '',
             '以下11维参数已分别抽取，必须逐项执行，不得擅自换成惯用组合：']
    lines.extend(f'{label}：{values[key].strip()}' for key, label in DIMENSIONS)
    if extra.strip():
        lines.extend(['', '补充要求：', extra.strip()])
    lines.extend(['', '参考图由我随本指令一并上传。请直接生成图片，不要只复述参数。'])
    return '\n'.join(lines)

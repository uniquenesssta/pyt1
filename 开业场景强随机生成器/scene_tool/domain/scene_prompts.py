"""Reference preservation and scene-specific prompt composition."""
from scene_tool.config.photography import photo_requirements
from scene_tool.domain.visibility import hidden_keys

REFERENCE_RULES = '参考图用途：保留参考装置的板材形状、数量、图案、文字、颜色和人物比例，不擅自替换姓名或添加品牌、地址及开业文案。尺寸遵循参考图及补充要求，未指定时按场地合理放置，不强制使用开业大板尺寸。气球配色跟随参考图，略微通透、高光自然。仅改变环境、摆位和拍摄构图；装置完整入镜。现场新增装饰仅使用板材与气球，不添加实体花艺、花篮、花束或花墙；保留板面的印刷花卉图案。'

def make_scene_prompt(profile, values, extra, hidden=None):
    hidden = hidden_keys(hidden)
    if any(not values[k].strip() for k in [d['key'] for d in profile['dimensions'] if d['key'] not in hidden]):
        raise ValueError('请填写全部场景参数。')
    photo = photo_requirements(values.get("camera", ""), "camera" in hidden).replace('开业现场照片', '现场照片').replace('店内现有灯光', '现场现有灯光')
    lines = [photo, '', REFERENCE_RULES, '', '当前场景：' + profile['name'],
             '场景边界：' + profile['rules'],
             '拍摄范围：' + profile['environment'],
             '装置周围预留通行空间；气球固定可靠。人物不遮挡主要图案和文字，不要求摆拍。', '', '本轮随机参数：']
    if profile['environment'] == '室内':
        lines.insert(-2, '全部拍摄发生在室内，不出现室内车辆；时段只影响现有室内光线和窗外。')
    lines += [d['label'] + '：' + values[d['key']] for d in profile['dimensions'] if d['key'] not in hidden]
    if extra.strip():
        lines += ['', '补充要求：', extra.strip()]
    return '\n'.join(lines)



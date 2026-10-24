"""Adapt generated camera and default scene wording to the selected intent."""
from scene_tool.config.render_styles import COMMERCIAL
from scene_tool.config.defaults import DEFAULT_CONSTRAINTS


def styled_values(values, style):
    result = dict(values)
    if style == COMMERCIAL and 'camera' in result:
        camera = result['camera']
        for old, new in (
            ('手持手机后置长焦镜头', '相机长焦镜头'),
            ('手持手机拍摄', '稳定相机拍摄'), ('手持手机', '稳定相机'),
            ('后置主摄1倍', '所选镜头'), ('手机后置主摄', '相机'),
            ('随手拍', '严谨构图'),
        ):
            camera = camera.replace(old, new)
        result['camera'] = camera
    return result


def styled_constraints(constraints, style):
    if style == COMMERCIAL and constraints == DEFAULT_CONSTRAINTS:
        return constraints.split('生活化细节：')[0].rstrip().replace('开业文案和地址', '开业文案').replace('品牌和地址', '品牌').replace('根据本轮建筑和摆位提供足够的实际空间；门廊、树荫与街道的明暗差应符合当前天气和时段，不把阴影处照成均匀棚拍光。', '根据商业展示空间、背景层次和装置构图布置环境，光线按本轮商业灯光执行。') + '\n\n商业画面整理：主体周围保持整洁，默认不安排路人和车辆遮挡或干扰装置；保留自然真实的场所背景。'
    return constraints


def styled_environment(text, style):
    if style == COMMERCIAL:
        return text.replace('可有0—3位顾客或工作人员，', '默认不安排顾客或工作人员入镜，').replace('使用室内现有灯光', '使用本轮商业光线与适度补光')
    return text

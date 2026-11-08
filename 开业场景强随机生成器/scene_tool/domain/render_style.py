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
        return constraints.split('生活化细节：')[0].rstrip().replace('开业文案和地址', '开业文案') + '\n商业画面整理：默认无人，保持真实场所背景，布光按本轮商业光线执行。'
    return constraints


def styled_environment(text, style):
    if style == COMMERCIAL:
        return text.replace('可有0—3位顾客或工作人员，', '默认不安排顾客或工作人员入镜，').replace('使用室内现有灯光', '使用本轮商业光线与适度补光')
    return text

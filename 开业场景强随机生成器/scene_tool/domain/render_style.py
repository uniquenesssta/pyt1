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
        return constraints.split('生活化细节：')[0].rstrip() + '\n\n商业画面整理：主体周围保持整洁，默认不安排路人和车辆遮挡或干扰装置；保留自然真实的场所背景。'
    return constraints


def styled_environment(text, style):
    if style == COMMERCIAL:
        return text.replace('可有0—3位顾客或工作人员，', '默认不安排顾客或工作人员入镜，')
    return text

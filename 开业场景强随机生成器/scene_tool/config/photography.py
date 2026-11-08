"""Shared photographic intent and permitted physical decorations."""
PHOTO_REQUIREMENTS = """照片要求：生成一张未经精修的真实手机开业现场照片（candid smartphone photo）。
手机自然持于胸口至眼睛高度，用后置主摄1倍拍摄；正常步行机位，后退容纳完整装置。不仰拍、抬高俯拍或使用超广角。
使用现场自然光和店内现有灯光，曝光自然，景深符合手机主摄，保留轻微明暗不均与使用痕迹。
天气只影响现场时段与采光，不额外安排地面反光。不要3D渲染、棚拍布光、夸张HDR、做旧或添加噪点。"""
DECORATION_REQUIREMENTS = """装饰范围：现场新增装饰只使用KT板和气球，不添加实体花艺、花篮或花墙；参考现场的实体花艺移除，板面印刷图案保留。"""



def photo_requirements(camera='', camera_hidden=False, render_style=None):
    from scene_tool.config.render_styles import COMMERCIAL, COMMERCIAL_REQUIREMENTS, COMMERCIAL_CAMERA_RULE
    if render_style == COMMERCIAL:
        text = COMMERCIAL_REQUIREMENTS
        if camera_hidden:
            text = text.replace(COMMERCIAL_CAMERA_RULE, '')
        return text
    text = PHOTO_REQUIREMENTS
    if camera_hidden or ('等效' in camera and 'mm' in camera):
        text = text.replace('后置主摄', '后置相机')
        text = text.replace('用后置相机1倍拍摄', '使用本轮指定的等效焦段拍摄' if not camera_hidden else '自然手持拍摄')
        text = text.replace('景深符合手机主摄', '景深符合实际焦段和拍摄距离')
    return text

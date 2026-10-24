"""Commercial display dimensions for the seven non-opening scenes."""
from copy import deepcopy
from scene_tool.config.render_styles import COMMERCIAL


def scene_profile(profile, style):
    if style != COMMERCIAL:
        return profile
    result = deepcopy(profile)
    ds = result['dimensions']
    for index in (0, 1, 3, 4):
        ds[index]['options'] = [value + '；商业展示整理，背景简洁、材质真实，不抢装置主体' for value in ds[index]['options']]
    ds[2]['label'] = '商业装置布局'
    ds[2]['options'] = [value + '；' + layout for value in profile['dimensions'][2]['options'][:8]
                         for layout in ('主体居中，左右均衡', '主体偏左，右侧留白', '主体偏右，左侧留白', '前后分层，主体完整')]
    ds[5]['label'] = '主体展示构图'
    ds[5]['options'] = [a + '；' + b + '；默认无人，不添加行人和车辆'
                       for a in ('主体居中', '主体位于左侧三分线', '主体位于右侧三分线', '主体占画面主要区域')
                       for b in ('背景简洁留白', '空间线条引导视线', '装置与背景拉开层次', '保留适量真实环境')]
    ds[6]['options'] = [a + '；' + b + '；配色跟随参考图，微透柔和，不遮挡板面'
                       for a in ('单侧气球框景', '两侧高低气球簇', '非对称气球半环', '底部气球群与侧边竖簇')
                       for b in ('疏密渐变', '大小错落', '轮廓简洁', '局部聚拢')]
    ds[7]['label'] = '商业拍摄角度'
    ds[8]['label'] = '商业光线'
    ds[8]['options'] = ['柔和侧光与正面补光', '均匀明亮展示光', '暖色背景配中性主体光', '柔和漫射光，色彩准确', '自然光方向配适度补光', '柔和逆侧光，板面充分补光']
    return result

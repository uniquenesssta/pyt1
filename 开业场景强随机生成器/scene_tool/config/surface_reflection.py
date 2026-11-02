"""Visible surface highlights, independent of the studio setup and material."""
KEY = 'detail_reflection'
LABEL = '表面反光'
OPTIONS = (
    '跟随材质：按参考或指定材质的真实光泽表现',
    '近乎无反光：避开直射亮斑，保留底色和自然明暗',
    '轻微柔光：仅在迎光处留一层淡亮，不遮住图文',
    '宽幅柔光：在材质能反光的区域保留宽而柔和的亮带',
    '侧缘高光：让已有光泽沿一侧边缘显现，正面仍能读清',
    '局部亮斑：仅在本身有光泽的部位保留小片亮斑，不泛白',
    '明显镜面反射：仅限真实高光泽表面；哑光材料仍按哑光表现',
)


def dimension():
    return {'key': KEY, 'label': LABEL, 'options': list(OPTIONS)}


def prompt_value(value):
    return value + '。通过灯位与柔光控制可见反光；以实际材质为限，不为达到此效果添加覆膜或金属工艺。'

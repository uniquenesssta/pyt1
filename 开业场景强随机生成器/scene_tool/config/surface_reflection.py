"""Short UI labels, their visible result, and migration of shipped reflection presets."""
KEY = 'detail_reflection'
LABEL = '表面反光'
AUTO, MATTE, SOFT, GLOSS, HIGH = OPTIONS = ('跟随材质', '哑光', '微光', '亮面', '高光')
_DESCRIPTIONS = {
    AUTO: '保留参考产品的实际光泽',
    MATTE: '表面有明暗层次，但看不见明显反光带',
    SOFT: '同一色块仅在迎光处稍浅，其余保持原色，亮度变化轻微',
    GLOSS: '能看见清楚的柔边反光带，带内比带外亮',
    HIGH: '反光明显，亮部仍看得清原有细节，不泛白',
}
# Match exact shipped strings only; handwritten instructions remain user data.
_LEGACY = dict(zip((
    '跟随材质：按参考或指定材质的真实光泽表现',
    '近乎无反光：避开直射亮斑，保留底色和自然明暗',
    '轻微柔光：仅在迎光处留一层淡亮，不遮住图文',
    '宽幅柔光：在材质能反光的区域保留宽而柔和的亮带',
    '侧缘高光：让已有光泽沿一侧边缘显现，正面仍能读清',
    '局部亮斑：仅在本身有光泽的部位保留小片亮斑，不泛白',
    '明显镜面反射：仅限真实高光泽表面；哑光材料仍按哑光表现',
), (AUTO, MATTE, SOFT, GLOSS, GLOSS, HIGH, HIGH)))


def normalize(value):
    return _LEGACY.get(value, value)


def dimension():
    return {'key': KEY, 'label': LABEL, 'options': list(OPTIONS)}


def prompt_value(value):
    value = normalize(value)
    detail = _DESCRIPTIONS.get(value)
    return (value + '。' + detail if detail else value) + '；保留原材质。'

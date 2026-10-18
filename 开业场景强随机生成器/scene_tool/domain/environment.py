"""Resolve indoor placement and camera wording without changing saved choices."""


def scene_parameters(values):
    result = dict(values)
    if values.get('environment') != '室内':
        return result
    camera = values['camera']
    for original, replacement in (
        ('街道对面的人行道上', '大厅另一侧'), ('沿街步行区域', '室内通道旁'),
        ('人行道上', '室内空地上'), ('门廊外侧', '大厅入口内侧'),
        ('周围店面', '周围室内环境'), ('店面', '室内装置'), ('店门', '室内入口'),
    ):
        camera = camera.replace(original, replacement)
    result['camera'] = camera
    return result


def environment_instructions(values):
    if values.get('environment') == '室内':
        return ('场地要求：KT板、气球和拍摄者均位于门店室内。室内规则优先于模板中的街道、门廊描述；'
                '采用本轮室内摆位与气球造型；预留完整大板、支架和通行空间，气球高度适应实际层高，不遮挡消防设施与出入口。天气仅用于窗外或门外及自然采光，不在室内制造天气效果。'
                '使用室内现有灯光；可有0—3位顾客或工作人员，室内不出现车辆。')
    return '场地要求：KT板、气球和拍摄者均在室外，按本轮建筑、摆位和天气拍摄；气球使用可靠支架、配重或固定点，不让散球滚入车道，不占用主要通道。'


def dimension_label(key, label, values):
    return "内部装潢风格" if key == "architecture" and values.get("environment") == "室内" else label

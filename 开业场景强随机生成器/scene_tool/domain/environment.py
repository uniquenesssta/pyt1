"""Resolve indoor placement and camera wording without changing saved choices."""


def scene_parameters(values):
    result = dict(values)
    if values.get('environment') != '室内':
        return result
    result['architecture'] = '门店室内空间；装修材质和风格参考“' + values['architecture'] + '”，不是拍摄建筑外立面'
    placement = values['placement']
    for original, replacement in (
        ('入口', '室内入口'), ('建筑外墙前', '室内背景墙前'),
        ('临街转角外侧', '室内转角墙旁'), ('门廊深处', '大厅深处'),
        ('庭院', '大厅'), ('店前平台', '室内大厅'), ('沿街窗面', '室内窗边'),
        ('台阶下方侧边空地', '室内楼梯旁空地'), ('外摆区后侧', '室内休息区后侧'),
        ('骑楼柱间', '大厅立柱之间'), ('转角侧立面', '室内转角墙前'),
        ('前庭绿植旁', '室内绿植旁'), ('门前空地', '室内入口旁空地'),
    ):
        placement = placement.replace(original, replacement)
    result['placement'] = placement
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
                '采用下列转换后的室内摆位与视角。天气仅用于窗外或门外及自然采光，不在室内制造天气效果。'
                '使用室内现有灯光；可有0—3位顾客或工作人员，室内不出现车辆。')
    return '场地要求：KT板、气球和拍摄者均在室外，按本轮建筑、摆位和天气拍摄。'

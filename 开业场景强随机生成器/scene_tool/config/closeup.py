"""Subject, framing and camera choices for the independent close-up style."""
CLOSEUP = '近景摄影'
FOCUS = ('最能辨认对象的一处轮廓', '表面质感最清楚的一小块区域', '主体边缘与背景的交界', '外形转折处', '受光面与阴影的过渡', '一处具有代表性的真实细节')
CROPS = ('局部居中，边缘留少量空间', '主体偏左，右侧留少量环境', '主体偏右，左侧留少量环境', '紧凑取景，以局部填满大部分画面', '稍宽的近景，保留相邻部件作为尺度参照', '沿局部轮廓安排对角线构图')
ANGLES = tuple(f'{angle}，{height}，自然手持，对焦本轮细节主体，不使用超广角' for angle in ('正面平视', '左前方约15度', '右前方约15度', '左前方约30度', '右前方约30度', '从略高处轻微向下观察') for height in ('胸口高度', '眼睛高度'))
REQUIREMENTS = '请为【{subject}】拍摄一张写实近景照片。选择它本身确实存在的一处代表性细节作为焦点，让其余部分自然落在画外。保留真实比例、轮廓、颜色和材质；有参考图时以参考图为准，没有标注尺寸时不猜测大小。采用符合现场的柔和光线，焦点清晰，保留自然景深，不额外添加道具、文字或装饰。'


def closeup_brief(subject):
    return REQUIREMENTS.format(subject=(subject or '').strip() or '参考图中的主体')

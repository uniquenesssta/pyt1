"""Subject, framing and camera choices for the independent close-up style."""
from scene_tool.config.material_surface import material_brief
from scene_tool.config.material_finish import FOLLOW, normalize as normalize_finish

CLOSEUP = '近景摄影'
FOCUS = ('最能辨认对象的一处轮廓', '可辨识的主要细节及其相邻轮廓', '主体边缘与背景的交界', '外形转折处', '受光面与阴影的过渡', '一处具有代表性的真实细节')
CROPS = ('局部居中，边缘留少量空间', '主体偏左，右侧留少量环境', '主体偏右，左侧留少量环境', '主体局部占主要区域，同时留出一侧相邻细节', '稍宽的近景，保留相邻部件作为尺度参照', '沿局部轮廓安排对角线构图', '让已有边缘连续穿过两个画边，背景只露窄缝', '让原有轮廓从一侧画边进入，以相邻边线交代产品走向')
# Describe the lens relative to the visible surface, independent of product size.
LEGACY_ANGLES = (
    '正对局部表面，镜头轴线垂直于该处表面；平放物从正上方俯拍，保持边缘比例',
    '垂直俯拍，绕镜头轴线轻转取景，让原有长边从左上斜穿画面至右下，不制造透视收缩',
    '垂直俯拍，反向旋转取景，让原有边缘从左下延伸至右上，不旋转或拉伸图案本身',
    '接近正俯拍，从左侧略微偏离表面法线，让近侧边缘带出轻微厚度',
    '接近正俯拍，从右侧略微偏离表面法线，保留主体与相邻区域的边界',
    '从左前上方斜俯拍，沿主体原有走势取景，保留由近及远的尺度变化',
    '从右前上方斜俯拍，将焦点落在局部轮廓转折处，允许远端自然出画',
    '低机位沿表面纵向斜拍，焦点落在近端，视线向远端延伸，背景自然变软',
    '从侧边压低镜头，沿表面横向斜拍，对焦边缘附近的纹理，保留自然厚度',
    '从边角外侧向内斜俯拍，让两条可见轮廓在画内相交，不要求整个对象入镜',
    '镜头正对代表性细节，取入相邻边缘作为尺度参照，外围自然截断，清晰面保持平整',
    '从侧上方沿可见边缘拍摄；已有叠层时以交界处为焦点，单件只拍自身边界',
)
from scene_tool.config.studio_shots import choices, camera_family, SHOTS, FLAT, ALONG, CORNER

ANGLES = choices('camera')
LEGACY_CAMERA_MAP = {
    old: SHOTS[name]['camera'][index]
    for old, (name, index) in zip(LEGACY_ANGLES, (
        (FLAT, 3), (FLAT, 0), (FLAT, 1), (ALONG, 0), (ALONG, 1), (ALONG, 0),
        (ALONG, 1), (ALONG, 2), (ALONG, 3), (CORNER, 0), (FLAT, 3), (CORNER, 2),
    ))
}
REQUIREMENTS = """为【{subject}】生成商品详情页用的专业单反棚拍近景（photorealistic）。干净哑光棚台，画内只留产品与必要台面。
以全画幅单反、90–105mm微距镜头成像为参考；取入主要细节和一处相邻结构，不做极限放大。机位、裁切和对焦按本轮参数执行。
产品原稿决定形状、数量、图文、配色和比例；实物材质图决定表面外观。拍摄样片只参考机位与布光，不移植其图案或道具。
可控棚灯，曝光与色彩自然，保留图文、真实轮廓、底色和明暗过渡；不额外强化纹理、锐化白边或添加假散景。"""


def closeup_brief(subject, material=None, camera=None, finish=None):
    description = material_brief(material)
    finish = normalize_finish(finish)
    if finish != FOLLOW:
        description += f' 材质表面：{finish}。'
    subject = (subject or '').strip()
    layout = ''
    if any(word in subject for word in ('对联', '春联', '联幅')):
        layout = '\n对联取景：按原稿保留字形、字距及边饰；参考确有多幅时才带入相邻联幅，单幅绝不复制。不把完整大字居中放满。'
    return REQUIREMENTS.format(subject=(subject or '').strip() or '参考图中的主体') + '\n' + description + layout + (f'\n本轮棚拍镜头：{camera_family(camera)}。' if camera_family(camera) else '')

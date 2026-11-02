"""Subject, framing and camera choices for the independent close-up style."""
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
REQUIREMENTS = '''为【{subject}】拍摄一张可用于商品详情页的专业单反棚拍商品近景。使用干净的哑光棚拍台，画面只露产品和必要的台面。以全画幅单反配90–105mm微距镜头的成像为基准，稳定机位、低ISO，按细节厚度收光圈，让选定部位清楚可辨。
镜头可对焦近处，但取景不等于极限微距。画面同时容纳主要细节和一处相邻结构，先看清产品，再看到表面质感，保留比例、字形、图案、配色及表面结构，不重绘、不猜测尺寸。产品原稿决定产品外观；拍摄样片只参考机位、取景和布光，不移植样片上的文字、纹样、颜色或道具。
用可控柔光塑造材质，按实物校准白平衡和曝光，保住高光纹理与暗部层次。边缘干净，无锐化白边、假散景或夸张HDR，不额外添加道具和装饰。'''


def closeup_brief(subject, material=None, camera=None):
    material = (material or '').strip()
    description = ('指定材质：' + material + '。按此材质呈现纹理与反光，不擅自添加其他工艺。' if material else '材质按参考图可见特征表现，不推测未指定的材质或工艺。')
    subject = (subject or '').strip()
    layout = ''
    if any(word in subject for word in ('对联', '春联', '联幅')):
        layout = '\n对联取景：保留原稿的字形、字距、边饰和相对大小，按本轮镜头取景，让画内可见的笔画、边饰或边角保持原有关系。若参考中确有多幅，可让另一幅仅从画边带入；单幅绝不复制。不把一个完整大字居中放满，不擅自增加金纹、龙纹或文字。'
    if '写真布' in material:
        description += '印刷图文为第一视觉层；布纹仅在焦点附近细微可见，不夸大为粗织网格。印刷金色保持原稿色调，不模拟未指定的金箔、压纹或金属闪光。' if not any(x in material for x in ('烫金', '金箔', '压纹')) else '按指定工艺局部表现，布纹不盖过图文。'
    return REQUIREMENTS.format(subject=(subject or '').strip() or '参考图中的主体') + '\n' + description + layout + (f'\n本轮棚拍镜头：{camera_family(camera)}。' if camera_family(camera) else '')

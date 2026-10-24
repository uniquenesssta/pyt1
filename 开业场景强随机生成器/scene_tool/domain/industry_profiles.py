"""Industry-specific spatial and graphic candidates, independent of UI state."""
import json
from functools import lru_cache
from scene_tool.config.paths import RESOURCES
from scene_tool.config.render_styles import COMMERCIAL
from scene_tool.config.defaults import DIMENSIONS

COMMERCIAL_DIMENSIONS = tuple((('display_space', '商业展示空间') if k == 'city' else
                              ('background_depth', '背景层次') if k == 'address' else
                              (k, '空间设计风格') if k == 'architecture' else
                              (k, '装置构图布局') if k == 'placement' else
                              (k, '商业光线') if k == 'lighting' else (k, label))
                             for k, label in DIMENSIONS)
EXTRA_DIMENSIONS = (('display_space', '商业展示空间'), ('background_depth', '背景层次'))


def dimensions(style):
    return COMMERCIAL_DIMENSIONS if style == COMMERCIAL else DIMENSIONS


def industry_key(value):
    return value if value in ('美业', '服装', '咖啡', '餐饮', '花店', '家居') else '通用'


@lru_cache(maxsize=7)
def profile(value):
    return json.loads((RESOURCES / 'industries' / (value + '.json')).read_text(encoding='utf-8'))


def industry_pools(industry, environment, style):
    data = profile(industry_key(industry))
    indoor = environment == '室内'
    commercial = style == COMMERCIAL
    positions = data['inside_positions' if indoor else 'outside_positions']
    spaces = data['interiors' if indoor else 'exteriors']
    layouts = ('主体居中，气球两侧均衡', '主体偏左，右侧保留背景', '主体偏右，左侧保留背景',
               '板材与气球高低错落', '主体前置，背景后退形成层次', '单侧气球框景，主板完整突出')
    balloons = ('单侧气球长簇', '左右高低气球簇', '不对称半包围气球框', '低位气球团与侧边竖簇', '疏密渐变气球带', '错落三组气球簇')
    result = {
      'architecture': [x + '；' + detail for x in spaces for detail in
                       (('界面整洁，突出材质和品牌气质', '简化背景杂物，保留空间层次', '以清晰线条和留白衬托产品') if commercial else
                        ('保留日常使用痕迹', '陈列疏密自然，符合实际经营空间', '保留真实门窗和通行动线'))],
      'placement': [x + '；' + detail for x in positions for detail in
                    (layouts if commercial else ('装置完整展示，留出通道', '稍偏向一侧，保留周围场景', '与原有陈列错开，避免遮挡'))],
      'balloons': [x + '；' + ('适应层高，稳固靠边摆放' if indoor else '独立配重固定，适应室外微风') + '；' + detail
                   for x in balloons for detail in ('柔和微透，颜色跟随参考图', '高低错落，保留板面文字', '疏密有序，气球不遮挡主要图案')],
      'brand': data['brands'], 'logo_shape': data['logos'],
      'logo_structure': [x + '；' + detail for x in ('图标在上字标在下', '图标在左字标在右', '图形与品牌文字穿插', '品牌字标为主小图标辅助')
                         for detail in ({'美业': ('纤细柔和留白', '精致圆润规整', '轻盈舒展主次'), '服装': ('时尚刊物式留白', '字标规整紧凑', '图文错位主次'), '咖啡': ('杯标式集中布局', '手作质感留白', '招牌字标主次'), '餐饮': ('清晰醒目紧凑布局', '餐牌式规整层次', '大字主标小图辅助'), '花店': ('纤细花礼式留白', '轻盈线描组合', '柔和疏朗层次')}.get(industry_key(industry), ('简洁留白', '紧凑规整', '明确主次')))],
    }
    if commercial:
        result['display_space'] = [v + '；' + x for v in data['venues'] for x in
                                  (('独立室内品牌展示区', '营业空间内的产品展示角', '接待前厅商业展示位') if indoor else
                                   ('门店外独立迎宾展示区', '外立面旁商业展示位', '门口步行空间内的品牌展示区'))]
        result['background_depth'] = [a + '；' + b for a in ('背景近距离简洁衬托', '中景保留空间轮廓', '远景形成自然纵深', '前中后景分层')
                                      for b in ('背景低对比不抢主体', '一侧留白衬托装置', '建筑线条引导视线', '材质层次清楚不过度虚化')]
        result['lighting'] = ['柔和侧光配适度补光', '均匀明亮的商业展示光', '柔和逆侧光勾勒板材，正面补光', '自然窗光方向加柔和补光', '阴天漫射光质感，主体曝光准确', '暖色环境光配中性主体光']
    return result

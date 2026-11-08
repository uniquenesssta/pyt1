"""Switchable image intent; the buyer-photo template remains the default."""
BUYER = '真实买家秀'
COMMERCIAL = '商业效果图'
from scene_tool.config.closeup import CLOSEUP
RENDER_STYLES = (BUYER, COMMERCIAL, CLOSEUP)

COMMERCIAL_CAMERA_RULE = '使用本轮75—150mm等效长焦和正面、左前或右前视角，相机水平，后退取景，不改用广角。'
COMMERCIAL_REQUIREMENTS = """商业效果图要求：生成用于商品展示的高品质写实场景效果图（photorealistic），专业精修，主体完整，文字清楚，空间关系可信。
""" + COMMERCIAL_CAMERA_RULE + """
按本轮光线布光，可适度补光；主体与背景分明，色彩自然，气球微透且高光柔和，避免金属质感。
保留参考设计及人物比例，背景整洁；不新增道具、水印、噪点、发光描边或镜面地面。"""


def normalize_style(value):
    if value == '商业主图':
        return COMMERCIAL
    return value if value in RENDER_STYLES else BUYER

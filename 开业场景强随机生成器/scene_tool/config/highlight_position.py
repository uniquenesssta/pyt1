"""Where the studio light is reflected on the product as viewed by the camera."""
from scene_tool.config import surface_reflection as surface

KEY, LABEL = 'detail_light', '亮光位置'
NONE, SIDES, CENTER, LEFT, RIGHT = OPTIONS = (
    '无明显光带', '两侧亮，中间不亮', '中间亮，两侧不亮', '左侧亮，右侧不亮', '右侧亮，左侧不亮',
)
_DIRECTIONS = {
    NONE: '移开直射反光，图文正常曝光，表面没有亮带。',
    SIDES: '调整左右两块柔光面，只在产品两侧各留一道柔边亮带；中间保留原色，不出现亮带。',
    CENTER: '调整矩形柔光箱，让产品中部出现一道连续的宽亮带；两侧保留原色，没有亮带。',
    LEFT: '调整灯位，让柔边亮带落在产品左侧，右侧保留原色。',
    RIGHT: '调整灯位，让柔边亮带落在产品右侧，左侧保留原色。',
}
# The old light presets described illumination, not an explicit highlight position.
LEGACY = (
    '大柔光箱从侧上方均匀照亮整段产品，反侧白卡轻补，色块稳定',
    '高位漫射主光覆盖画幅，压低镜面眩光，保留原有深浅色的分界',
    '大面积侧柔光横过展示面，黑旗收住反光，近端细节保持本色',
    '从斜上方宽柔光补亮主体，让远近层次来自透视和焦点',
    '侧上方大柔光配轻补光，已有叠层只留一线接触阴影',
    '柔光沿边角落下，保住边缘明暗差，不凭空制造悬浮层',
    '大面积侧柔光，另一侧白卡轻补，保留细微纹理', '近轴柔光均匀覆盖主体，白平衡中性，色块不偏色',
    '宽柔光从侧上方照亮主体，让色块均匀、细微纹理自然可见', '用黑旗收住杂散反光，仅保留材质本身的光泽',
)


def compatible(strength, position):
    if strength in surface.OPTIONS and position in OPTIONS and strength != surface.AUTO:
        return (strength == surface.MATTE) == (position == NONE)
    return True


def prompt_value(value):
    detail = _DIRECTIONS.get(value)
    if not detail:
        return value
    return value + '。' + detail + ('带内仍看得清图文，不画白条。' if value != NONE else '')

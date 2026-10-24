"""Resolve selected physical geometry and remove the old universal large-board rule."""
from scene_tool.config.product_size import FOLLOW_REFERENCE, FIXED_LARGE, normalize_size

OLD_SIZE = 'KT板固定为3.5米宽、2.2米高的横版大板，照片画幅单独按本轮比例执行。'


def size_instructions(value):
    value = normalize_size(value)
    if value == FOLLOW_REFERENCE:
        detail = ('产品实际宽度、高度以参考图明确标注的尺寸为准；保留参考产品形状，'
                  '排除背景留白和拍摄透视，不把参考照片的画幅当成产品比例，不强制拉成矩形大板。'
                  '未提供实际尺寸或可靠尺度参照时，不凭照片编造米数，不强制指定产品宽高。')
    elif value == FIXED_LARGE:
        detail = 'KT板固定为3.5米宽、2.2米高的横版大板，保持真实大型板材尺度。'
    else:
        detail = ('采用用户指定的产品实际尺寸：' + value + '。宽度和高度按明确的物理单位执行。'
                  '保持参考设计，不拉伸人物和文字。')
    return '产品尺寸：' + detail + '产品本身比例与最终照片画面比例分别执行，照片画幅不能改变产品形状；本项优先于模板中的通用尺寸描述。'


def size_constraints(text, value):
    if normalize_size(value) == FIXED_LARGE:
        return text
    return (text.replace(OLD_SIZE, '产品尺寸按独立产品规格执行，照片画幅单独按本轮画面比例执行。')
            .replace('真实大型板材尺度', '实际产品尺度')
            .replace('仅参考KT板表面的平面设计与气球配色', '参考产品正面形状与比例、板面的平面设计及气球配色'))


def size_environment(text, value):
    if normalize_size(value) == FIXED_LARGE:
        return text
    return text.replace('完整大板', '完整产品')

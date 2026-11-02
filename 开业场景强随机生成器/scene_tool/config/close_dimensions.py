"""Shared vocabulary for photographing an existing product rather than redesigning it."""
from scene_tool.config.material_surface import SURFACE_OPTIONS, OLD_SURFACES
from scene_tool.config.closeup import FOCUS, CROPS
from scene_tool.config.studio_shots import SHOT_KEYS, choices

from scene_tool.config import highlight_position as position, surface_reflection as reflection

FIELDS = {
    reflection.KEY: (reflection.LABEL, reflection.OPTIONS),
    'detail_edge': ('邻接边缘', ('让相邻元素停在画边', '保留主体边缘轮廓', '只露出少量相邻区域', '沿主体外缘留出少量空间')),
    'detail_layers': ('前后层次', ('只从产品间隙或画边露出少量哑光台面', '相邻部件形成前后层次', '用原有边界区分相邻区域，不垫高主体', '压低背景对比突出局部')),
    'detail_space': ('局部留白', ('沿原有留白收边', '主体一侧多留少量空间', '四周紧凑但不切断识别点', '留出局部轮廓的呼吸空间')),
    'detail_focus': ('细节主体', FOCUS),
    'detail_surface': ('材质表现', SURFACE_OPTIONS),
    'detail_art': ('外观保留重点', ('保持局部真实形状', '保留已有可辨识细节', '保持原有颜色与明暗过渡', '不拉伸或美化主体轮廓')),
    'detail_crop': ('局部构图', CROPS),
    'detail_light': (position.LABEL, ('大面积侧柔光，另一侧白卡轻补，保留细微纹理', '近轴柔光均匀覆盖主体，白平衡中性，色块不偏色', '宽柔光从侧上方照亮主体，让色块均匀、细微纹理自然可见', '用黑旗收住杂散反光，仅保留材质本身的光泽')),
    'detail_plane': ('对焦层次', ('精确对焦关键轮廓，边界清楚不生硬', '按主体厚度控制景深，重要细节都在清晰范围内', '焦点落在主要细节与相邻结构交界处，两者的关系清楚可读', '让同一焦平面上的相邻细节保持一致清晰度')),
}

LEGACY_FIELDS = {k: FIELDS[k][1] for k in SHOT_KEYS if k in FIELDS}
for key in LEGACY_FIELDS:
    FIELDS[key] = (FIELDS[key][0], choices(key))


def upgrade_options(key, items):
    # Older editors saved complete default lists, even when only one field was edited.
    if key == 'detail_surface':
        return list(dict.fromkeys(OLD_SURFACES.get(x, x) for x in items))
    if key == reflection.KEY:
        return list(dict.fromkeys(reflection.normalize(x) for x in items))
    if key == position.KEY and any(x in position.LEGACY for x in items):
        return list(dict.fromkeys([*position.OPTIONS, *(x for x in items if x not in position.LEGACY)]))
    old = LEGACY_FIELDS.get(key, ())
    if not old or not any(x in old for x in items):
        return list(items)
    return list(dict.fromkeys([*choices(key), *(x for x in items if x not in old)]))


GROUPS = (('近景布置', ('detail_edge','detail_layers','detail_space')),
          ('近景内容', ('detail_focus','detail_surface','detail_art')),
          ('近景拍摄', ('detail_crop','camera',reflection.KEY,'detail_light','detail_plane','ratio')))
LABELS = {**{k:v[0] for k,v in FIELDS.items()}, 'environment':'室内 / 室外','camera':'近景机位','ratio':'画面比例'}
DIMENSIONS = tuple((k,LABELS[k]) for _,keys in GROUPS for k in keys)

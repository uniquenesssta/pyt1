"""Exact shipped preservation phrases already covered by the fixed reference brief."""
from scene_tool.config.material_surface import SURFACE_OPTIONS, OLD_SURFACES

COVERED = {
    'detail_surface': set(SURFACE_OPTIONS) | set(OLD_SURFACES),
    'detail_art': {'保持局部真实形状','保留已有可辨识细节','保持原有颜色与明暗过渡','不拉伸或美化主体轮廓'},
}

def covered(key,value):
    return value in COVERED.get(key, ())

def static_keys(pools,current):
    return {k for k,items in pools.items() if items and covered(k,current.get(k)) and all(covered(k,x) for x in items)}

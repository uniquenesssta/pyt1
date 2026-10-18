from scene_tool.config.defaults import DIMENSIONS
from scene_tool.config.interior_styles import INTERIOR_STYLES
from scene_tool.config.indoor_decor import INDOOR_PLACEMENTS, INDOOR_BALLOONS
from scene_tool.domain.scene_pools import EXTRA_LABELS

def validate_pools(value):
    if not isinstance(value, dict):
        raise ValueError('参数池必须是 JSON 对象。')
    result = {}
    for key, label in (*DIMENSIONS, *EXTRA_LABELS):
        fallback = {'interior': INTERIOR_STYLES, 'indoor_placement': INDOOR_PLACEMENTS,
                    'indoor_balloons': INDOOR_BALLOONS, 'environment': ['室内', '室外']}.get(key)
        items = value.get(key, fallback)
        if not isinstance(items, list) or not all(isinstance(x, str) and x.strip() for x in items):
            raise ValueError(f'{label}：必须是非空字符串列表。')
        items = list(dict.fromkeys(x.strip() for x in items))
        if len(items) < 2:
            raise ValueError(f'{label}：至少保留两个不同选项。')
        result[key] = items
    return result

def upgrade_pools(pools, defaults, legacy):
    """Upgrade untouched v1 pools, while preserving genuinely customized lists."""
    result = dict(pools)
    for key, previous in legacy.items():
        if result.get(key) == previous:
            result[key] = list(defaults[key])
    return validate_pools(result)

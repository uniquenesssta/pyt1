from scene_tool.config.defaults import DIMENSIONS
from scene_tool.config.interior_styles import INTERIOR_STYLES

def validate_pools(value):
    if not isinstance(value, dict):
        raise ValueError('参数池必须是 JSON 对象。')
    result = {}
    for key, label in (*DIMENSIONS, ('interior', '内部装潢风格')):
        fallback = INTERIOR_STYLES if key == 'interior' else ['室内', '室外'] if key == 'environment' else None
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

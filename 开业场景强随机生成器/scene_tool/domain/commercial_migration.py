"""Remove frame-position instructions from exact, previously shipped placements."""
from scene_tool.config.render_styles import COMMERCIAL

OLD_LAYOUTS = ('主体居中，左右均衡', '主体偏左，右侧留白', '主体偏右，左侧留白', '前后分层，主体完整')


def placement_updates(profile):
    return {value + '；' + layout: value
            for value in profile['dimensions'][2]['options'][:8] for layout in OLD_LAYOUTS}


def upgrade_commercial_state(profile, state):
    """Copy only known preset values; retain handwritten values and prompt edits."""
    result = dict(state)
    key = profile['dimensions'][2]['key']
    mapping = placement_updates(profile)
    overrides = state.get('commercial_pools', {})
    if isinstance(overrides, dict) and isinstance(overrides.get(key), list):
        result['commercial_pools'] = dict(overrides)
        old = overrides[key]
        # The exact old default list is not a user-defined restriction.
        if old == list(mapping):
            result['commercial_pools'].pop(key)
        else:
            result['commercial_pools'][key] = list(dict.fromkeys(mapping.get(v, v) for v in old))
    if state.get('render_style') in (COMMERCIAL, '商业主图'):
        result['values'] = dict(state.get('values', {}))
        old = result['values'].get(key)
        if old in mapping:
            result['values'][key] = mapping[old]
    return result

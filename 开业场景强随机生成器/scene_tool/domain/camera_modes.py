"""Resolve camera pools without changing scene placement or environment."""
from scene_tool.config.render_styles import COMMERCIAL
from scene_tool.config.camera_modes import COMMERCIAL_ANGLES, INDOOR_ANGLES


def camera_pool(outdoor, environment, style):
    if style == COMMERCIAL:
        return list(COMMERCIAL_ANGLES)
    if environment == '室内':
        return list(INDOOR_ANGLES)
    return list(outdoor)


def draw_camera(pool, previous, locked, bags, rng, strong=True):
    if locked and previous in pool:
        return previous
    key = 'camera_mode:' + ('commercial' if pool == list(COMMERCIAL_ANGLES) else 'indoor' if pool == list(INDOOR_ANGLES) else 'outdoor')
    if key == 'camera_mode:outdoor':
        key = 'camera'
    bag = bags.setdefault(key, [])
    bag[:] = [x for x in bag if x in pool]
    if not strong or not any(x != previous for x in bag):
        bag[:] = pool
    value = rng.choice([x for x in bag if x != previous] or bag)
    bag.remove(value)
    return value

"""Draw the family first, then sample only compatible visible field values."""
from scene_tool.config.closeup import LEGACY_CAMERA_MAP
from scene_tool.config.studio_shots import FLAT, SHOTS, SHOT_KEYS, camera_family, choices


class ShotConflict(ValueError):
    pass


def _pick(items, previous, rng, bags, key, strong):
    options = [x for x in items if x != previous] or list(items)
    if not strong:
        return rng.choice(options)
    bag = bags.setdefault('camera_mode:studio:' + key, [])
    bag[:] = [x for x in bag if x in items]
    if not bag or not any(x in options for x in bag):
        bag[:] = items
    value = rng.choice([x for x in bag if x in options])
    bag.remove(value)
    return value


def draw_shot(current, locked, pools, rng, bags, *, keep=False, strong=True):
    """Return new values and dropdown pools without mutating input values.

    Unclassified custom text is an explicit user choice, available across families.
    """
    locked = set(locked)
    current = dict(current)
    current['camera'] = LEGACY_CAMERA_MAP.get(current.get('camera'), current.get('camera'))
    valid = {}
    for name, shot in SHOTS.items():
        available = {}
        for key, pool in pools.items():
            allowed = [v for v in pool if key not in SHOT_KEYS or v in shot[key] or v not in choices(key)]
            old = current.get(key)
            if key in locked and old:
                if key in SHOT_KEYS and old in choices(key) and old not in shot[key]:
                    break
                if old not in allowed and key != 'camera' and (key not in SHOT_KEYS or old not in choices(key)):
                    allowed.append(old)
            if not allowed:
                break
            available[key] = allowed
        else:
            valid[name] = available
    if not valid:
        raise ShotConflict('锁定项或自定义候选池属于不同镜头，请解锁冲突项或调整候选，再重新随机。')
    old_family = camera_family(current.get('camera'))
    if keep and old_family in valid:
        family = old_family
    elif keep and not old_family and FLAT in valid:
        family = FLAT
    elif len(valid) == 1:
        family = next(iter(valid))
    else:
        family = _pick(list(valid), old_family, rng, bags, 'family', strong)
    selected = {}
    for key, allowed in valid[family].items():
        old = current.get(key)
        selected[key] = (old if (keep or key in locked) and old in allowed else
                         _pick(allowed, old, rng, bags, family + ':' + key, strong))
    return selected, valid[family]

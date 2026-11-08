"""Draw the family first, then sample only compatible visible field values."""
from scene_tool.config import highlight_position as pos, surface_reflection as surf
from scene_tool.config.closeup import LEGACY_CAMERA_MAP
from scene_tool.config.close_dimensions import normalize_value
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
    current = {k: normalize_value(k, v) for k, v in current.items()}
    current['camera'] = LEGACY_CAMERA_MAP.get(current.get('camera'), current.get('camera'))
    old_reflection = current.get(surf.KEY)
    current[surf.KEY] = surf.normalize(old_reflection)
    if current.get(pos.KEY) in pos.LEGACY:
        if current[surf.KEY] == surf.MATTE:
            current[pos.KEY] = pos.NONE
        elif old_reflection != current[surf.KEY] and old_reflection.startswith('侧缘高光：'):
            current[pos.KEY] = pos.LEFT
        else:
            current[pos.KEY] = pos.CENTER
    valid = {}
    pairs_by_family = {}
    lighting_conflict = False
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
            pairs = [(s, p) for s in available[surf.KEY] for p in available[pos.KEY]
                     if pos.compatible(s, p)
                     and (surf.KEY not in locked or not current.get(surf.KEY) or s == current[surf.KEY])
                     and (pos.KEY not in locked or not current.get(pos.KEY) or p == current[pos.KEY])]
            if pairs:
                valid[name] = available
                pairs_by_family[name] = pairs
            else:
                lighting_conflict = True
    if not valid:
        if lighting_conflict:
            raise ShotConflict('反光与亮光位置不匹配：哑光没有亮带。请解锁其中一项或调整候选。')
        raise ShotConflict('锁定项或自定义候选池属于不同镜头，请解锁冲突项或调整候选。')
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
    pairs = pairs_by_family[family]
    # Draw strength before position, including when the scene schema orders them differently.
    order = [surf.KEY, pos.KEY, *(k for k in valid[family] if k not in (surf.KEY, pos.KEY))]
    for key in order:
        allowed = valid[family][key]
        if key == surf.KEY:
            allowed = list(dict.fromkeys(s for s, _ in pairs))
        elif key == pos.KEY:
            allowed = [p for s,p in pairs if s == selected[surf.KEY]]
        old = current.get(key)
        if keep and old not in allowed:
            # A manual change of position should give a visible band, not an uncertain automatic finish.
            if key == surf.KEY:
                preferred = surf.MATTE if current.get(pos.KEY) == pos.NONE else surf.GLOSS
                if preferred in allowed:
                    old = preferred
            elif key == pos.KEY and pos.CENTER in allowed:
                old = pos.CENTER
        selected[key] = (old if (keep or key in locked) and old in allowed else
                         _pick(allowed, old, rng, bags, family + ':' + key, strong))
    return selected, valid[family]

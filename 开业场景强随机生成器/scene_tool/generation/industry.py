"""Independent shuffle bags for each industry, setting and image style."""
from scene_tool.domain.industry_profiles import industry_key


def draw_industry(engine, key, pool, previous, locked, industry, environment, style, strong=True):
    if locked and isinstance(previous, str) and previous.strip():
        return previous
    bag_key = 'industry:' + '|'.join((industry_key(industry), environment or '室外', style or '', key))
    bag = engine.bags.setdefault(bag_key, [])
    bag[:] = [x for x in bag if x in pool]
    if not strong or not any(x != previous for x in bag):
        bag[:] = pool
    candidates = [x for x in bag if x != previous] or bag
    family = (previous or '').split('；', 1)[0]
    different = [x for x in candidates if x.split('；', 1)[0] != family]
    selected = engine.rng.choice(different or candidates)
    bag.remove(selected)
    return selected

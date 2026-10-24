"""Independent shuffle bags for each industry, setting and image style."""
from scene_tool.domain.industry_profiles import industry_key


def draw_industry(engine, key, pool, previous, locked, industry, environment, style, strong=True):
    if locked and previous in pool:
        return previous
    bag_key = 'industry:' + '|'.join((industry_key(industry), environment or '室外', style or '', key))
    bag = engine.bags.setdefault(bag_key, [])
    bag[:] = [x for x in bag if x in pool]
    if not strong or not any(x != previous for x in bag):
        bag[:] = pool
    selected = engine.rng.choice([x for x in bag if x != previous] or bag)
    bag.remove(selected)
    return selected

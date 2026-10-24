import random
from scene_tool.domain.industry_profiles import dimensions, industry_pools
from scene_tool.generation.industry import draw_industry
from scene_tool.domain.camera_modes import camera_pool, draw_camera
from scene_tool.domain.scene_pools import pool_key as active_pool, INDOOR_KEYS
from scene_tool.config.defaults import DIMENSIONS
from scene_tool.domain.pools import validate_pools
from scene_tool.generation.unique import fresh_value

class Randomizer:
    """Each dimension has its own shuffle bag. Locks never consume bag entries.

    Strong mode exhausts every option before refilling; both modes avoid the
    immediately previous value. No shared index ties dimensions together.
    """
    def __init__(self, pools, rng=None, generated=True):
        self.pools = validate_pools(pools)
        self.rng = rng or random.SystemRandom()
        self.bags = {}
        self.industry_overrides = {}
        self.generated = generated
        self.recent = {"brand": [], "address": []}

    def scoped_pools(self, industry, environment, style):
        from scene_tool.domain.industry_profiles import industry_key
        pools = industry_pools(industry, environment, style)
        context = '|'.join((industry_key(industry), environment or '室外', style or ''))
        for key, items in self.industry_overrides.get(context, {}).items():
            if isinstance(items, list) and len(set(items)) >= 2 and all(isinstance(x, str) and x.strip() for x in items):
                pools[key] = list(items)
        return pools

    def restore_bags(self, bags):
        if not isinstance(bags, dict):
            return
        for key, items in bags.items():
            if key.startswith(('camera_mode:', 'industry:')) and isinstance(items, list):
                self.bags[key] = [x for x in items if isinstance(x, str)]
            if key in self.pools and isinstance(items, list):
                self.bags[key] = list(dict.fromkeys(x for x in items
                    if isinstance(x, str) and x in self.pools[key]))

    def restore_recent(self, recent):
        if isinstance(recent, dict):
            for key in self.recent:
                items = recent.get(key, [])
                if isinstance(items, list):
                    self.recent[key] = [x for x in items if isinstance(x, str)][-200:]

    def draw(self, current=None, locked=(), strong=True, render_style=None, industry=None):
        if render_style == '商业效果图' and industry is None:
            industry = '通用'
        current = current or {}
        result = dict(current)
        for key in ['environment'] + [k for k, _ in dimensions(render_style) if k != 'environment']:
            scoped = self.scoped_pools(industry, result.get('environment'), render_style) if industry is not None else {}
            if key in scoped:
                result[key] = draw_industry(self, key, scoped[key], current.get(key), key in locked, industry, result.get('environment'), render_style, strong)
                continue
            if key == 'camera':
                pool = camera_pool(self.pools['camera'], result.get('environment'), render_style)
                result[key] = draw_camera(pool, current.get(key), key in locked, self.bags, self.rng, strong)
                continue
            pool_key = active_pool(key, result.get('environment'))
            switched = key in INDOOR_KEYS and result.get('environment') != current.get('environment', '室外')
            if key in locked and current.get(key, '').strip() and not switched:
                continue
            previous = current.get(key)
            if self.generated and key in self.recent:
                value = fresh_value(key, self.rng, previous, self.recent[key])
                self.recent[key] = (self.recent[key] + [value])[-200:]
                result[key] = value
                continue
            if not strong:
                result[key] = self.rng.choice([x for x in self.pools[pool_key] if x != previous])
                continue
            bag = self.bags.setdefault(pool_key, [])
            if not bag:
                bag.extend(self.pools[pool_key])
                self.rng.shuffle(bag)
            candidates = [x for x in bag if x != previous]
            if not candidates:
                # A manual edit may equal the final remaining entry. Begin a new
                # cycle to prioritize never repeating the value currently shown.
                bag[:] = self.pools[pool_key]
                self.rng.shuffle(bag)
                candidates = [x for x in bag if x != previous]
            selected = self.rng.choice(candidates)
            bag.remove(selected)
            result[key] = selected
        return result


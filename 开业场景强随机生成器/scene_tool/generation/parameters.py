import random
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
        self.generated = generated
        self.recent = {"brand": [], "address": []}

    def restore_bags(self, bags):
        if not isinstance(bags, dict):
            return
        for key, items in bags.items():
            if key in self.pools and isinstance(items, list):
                self.bags[key] = list(dict.fromkeys(x for x in items
                    if isinstance(x, str) and x in self.pools[key]))

    def restore_recent(self, recent):
        if isinstance(recent, dict):
            for key in self.recent:
                items = recent.get(key, [])
                if isinstance(items, list):
                    self.recent[key] = [x for x in items if isinstance(x, str)][-200:]

    def draw(self, current=None, locked=(), strong=True):
        current = current or {}
        result = dict(current)
        for key in ['environment'] + [k for k, _ in DIMENSIONS if k != 'environment']:
            pool_key = 'interior' if key == 'architecture' and result.get('environment') == '室内' else key
            switched = key == 'architecture' and result.get('environment') != current.get('environment', '室外')
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

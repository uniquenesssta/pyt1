import random
from scene_tool.config.copy_phrases import HEADLINES, SUBLINES, SEPARATOR
from scene_tool.domain.industry_profiles import profile, industry_key

class CopyRandomizer:
    def __init__(self, rng=None):
        self.rng = rng or random.SystemRandom()
        self.recent = []

    def draw(self, current='', enabled=True, locked=False, industry=None):
        if not enabled or locked:
            return current
        # Finite enumeration guarantees termination even after a long history.
        sublines = profile(industry_key(industry))['copy'] if industry is not None else SUBLINES
        previous = current.split(SEPARATOR, 1)
        excluded = set(self.recent[-200:]) | {current}
        candidates = [h + SEPARATOR + s for h in HEADLINES for s in sublines
                      if h != previous[0]
                      and (len(previous) < 2 or s != previous[1])
                      and h + SEPARATOR + s not in excluded]
        if not candidates:
            candidates = [h + SEPARATOR + s for h in HEADLINES for s in sublines if h + SEPARATOR + s != current]
        value = self.rng.choice(candidates)
        self.recent = (self.recent + [value])[-200:]
        return value

    def restore(self, recent):
        if isinstance(recent, list):
            self.recent = [x for x in recent if isinstance(x, str)][-200:]


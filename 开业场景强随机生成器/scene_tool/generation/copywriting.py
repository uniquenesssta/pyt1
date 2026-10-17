import random
from scene_tool.config.copy_phrases import HEADLINES, SUBLINES, SEPARATOR

class CopyRandomizer:
    def __init__(self, rng=None):
        self.rng = rng or random.SystemRandom()
        self.recent = []

    def draw(self, current='', enabled=True, locked=False):
        if not enabled or locked:
            return current
        # Finite enumeration guarantees termination even after a long history.
        previous = current.split(SEPARATOR, 1)
        excluded = set(self.recent[-200:]) | {current}
        candidates = [h + SEPARATOR + s for h in HEADLINES for s in SUBLINES
                      if h != previous[0]
                      and (len(previous) < 2 or s != previous[1])
                      and h + SEPARATOR + s not in excluded]
        value = self.rng.choice(candidates)
        self.recent = (self.recent + [value])[-200:]
        return value

    def restore(self, recent):
        if isinstance(recent, list):
            self.recent = [x for x in recent if isinstance(x, str)][-200:]

"""Independent scene state, shuffle bags, editable prompts and reset snapshots."""
import random
from scene_tool.config.render_styles import normalize_style
from scene_tool.config.product_size import normalize_size
from scene_tool.domain.scene_prompts import make_scene_prompt




class SceneModel:
    def __init__(self, profile, state=None, rng=None):
        self.profile, self.rng = profile, rng or random.SystemRandom()
        state = state if isinstance(state, dict) else {}
        self.product_size = normalize_size(state.get('product_size'))
        self.render_style = normalize_style(state.get('render_style'))
        self.pools = {d['key']: list(d['options']) for d in profile['dimensions']}
        upgraded = set()
        for key, items in state.get('pools', {}).items():
            if key in self.pools and (items == profile.get('legacy_pools', {}).get(key) or
                                     (key == 'camera' and items == profile.get('legacy_camera'))):
                upgraded.add(key)
                continue
            if key in self.pools and isinstance(items, list) and len(set(items)) >= 2 and all(isinstance(x, str) and x.strip() for x in items):
                self.pools[key] = list(dict.fromkeys(items))
        values = state.get('values', {})
        self.values = {k: values.get(k, '') if isinstance(values.get(k, ''), str) else '' for k in self.pools}
        self.locks = {k: bool(state.get('locks', {}).get(k, False)) for k in self.pools}
        self.hidden = {k: state.get('hidden', {}).get(k) is True for k in self.pools}
        self.bags = {k: list(dict.fromkeys(x for x in state.get('bags', {}).get(k, []) if x in pool)) for k, pool in self.pools.items()}
        for key in upgraded:
            self.bags[key] = []
        self.extra = state.get('extra', '')
        if any(not isinstance(state.get(k, ''), str) for k in ('extra', 'prompt', 'rendered')):
            raise ValueError('场景文本必须是字符串')
        self.prompt = state.get('prompt', '')
        self.rendered = state.get('rendered', '')
        self.undo = None
        if not all(self.values.values()):
            self.draw()
        if not self.prompt:
            self.regenerate()

    def draw(self):
        for key, pool in self.pools.items():
            if self.locks[key] and self.values[key]:
                continue
            bag = self.bags[key]
            if not any(x != self.values[key] for x in bag):
                bag[:] = pool
            choices = [x for x in bag if x != self.values[key]]
            previous_family = self.values[key].split('；', 1)[0]
            different = [x for x in choices if x.split('；', 1)[0] != previous_family]
            selected = self.rng.choice(different or choices)
            bag.remove(selected)
            self.values[key] = selected

    def generate(self):
        return make_scene_prompt(self.profile, self.values, self.extra, self.hidden, self.render_style, self.product_size)

    def regenerate(self):
        self.prompt = self.rendered = self.generate()

    def reset(self):
        before = (self.extra, self.prompt, self.rendered)
        if any(not self.values[k].strip() for k in self.pools if not self.hidden[k]):
            raise ValueError('请填写全部场景参数。')
        self.extra = ''
        self.regenerate()
        if before != (self.extra, self.prompt, self.rendered):
            self.undo = before

    def undo_reset(self):
        if self.undo:
            self.extra, self.prompt, self.rendered = self.undo
            self.undo = None

    def set_pool(self, key, items):
        items = list(dict.fromkeys(x.strip() for x in items if x.strip()))
        if len(items) < 2:
            raise ValueError('每项至少保留两个不同候选。')
        if items != self.pools[key]:
            self.pools[key] = items
            self.bags[key] = []

    def state(self):
        return {key: getattr(self, key) for key in ('values', 'locks', 'hidden', 'render_style', 'product_size', 'pools', 'bags', 'extra', 'prompt', 'rendered')}


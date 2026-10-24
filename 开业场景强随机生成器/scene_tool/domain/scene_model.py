"""Independent scene state, shuffle bags, editable prompts and reset snapshots."""
import random
from scene_tool.domain.camera_modes import camera_pool, draw_camera
from scene_tool.domain.commercial_scenes import scene_profile
from scene_tool.config.render_styles import COMMERCIAL
from scene_tool.generation.industry import draw_industry
from scene_tool.config.render_styles import normalize_style
from scene_tool.config.product_size import normalize_size
from scene_tool.domain.scene_prompts import make_scene_prompt




class SceneModel:
    def __init__(self, profile, state=None, rng=None):
        self.profile, self.rng = profile, rng or random.SystemRandom()
        state = state if isinstance(state, dict) else {}
        self.commercial_pools = state.get('commercial_pools', {}) if isinstance(state.get('commercial_pools', {}), dict) else {}
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
        mode_bags = {k: v for k, v in state.get('bags', {}).items() if k.startswith(('camera_mode:', 'industry:'))}
        mode_bags.update(state.get('camera_mode_bags', {}))
        for key, bag in mode_bags.items():
            if key.startswith(('camera_mode:', 'industry:')) and isinstance(bag, list):
                self.bags[key] = [x for x in bag if isinstance(x, str)]
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

    def active_profile(self):
        return scene_profile(self.profile, self.render_style)

    def active_pools(self):
        if self.render_style != COMMERCIAL:
            return self.pools
        pools = {d['key']: list(d['options']) for d in self.active_profile()['dimensions']}
        for key, items in self.commercial_pools.items():
            if key in pools and isinstance(items, list) and len(items) >= 2:
                pools[key] = items
        return pools

    def camera_pool(self):
        return camera_pool(self.pools['camera'], self.profile['environment'], self.render_style)

    def draw(self):
        for key, pool in self.active_pools().items():
            if key == 'camera':
                self.values[key] = draw_camera(self.camera_pool(), self.values[key], self.locks[key], self.bags, self.rng)
                continue
            if self.render_style == COMMERCIAL:
                self.values[key] = draw_industry(self, key, pool, self.values[key], self.locks[key], '通用', self.profile['environment'], self.render_style)
                continue
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
        return make_scene_prompt(self.active_profile(), self.values, self.extra, self.hidden, self.render_style, self.product_size)

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
        return {key: getattr(self, key) for key in ('values', 'locks', 'hidden', 'render_style', 'product_size', 'commercial_pools', 'pools', 'bags', 'extra', 'prompt', 'rendered')}


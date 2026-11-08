"""Independent scene state, shuffle bags, editable prompts and reset snapshots."""
import random
from scene_tool.config.random_strategy import normalize as normalize_strategy
from scene_tool.config import surface_reflection as reflection
from scene_tool.domain.camera_modes import camera_pool, draw_camera
from scene_tool.domain.commercial_scenes import scene_profile
from scene_tool.domain.commercial_migration import upgrade_commercial_state
from scene_tool.config.render_styles import COMMERCIAL
from scene_tool.generation.industry import draw_industry
from scene_tool.config.render_styles import normalize_style
from scene_tool.config.product_size import normalize_size
from scene_tool.domain.scene_prompts import make_scene_prompt




class SceneModel:
    def __init__(self, profile, state=None, rng=None):
        self.profile, self.rng = profile, rng or random.SystemRandom()
        state = upgrade_commercial_state(profile, state if isinstance(state, dict) else {})
        self.random_strategy = normalize_strategy(state.get('random_strategy'))
        step = state.get('strategy_step', 0)
        self.strategy_step = step if type(step) is int and step >= 0 else 0
        self.closeup_pools = state.get('closeup_pools', {})
        self.commercial_pools = state.get('commercial_pools', {}) if isinstance(state.get('commercial_pools', {}), dict) else {}
        self.close_subject = state.get('close_subject', '')
        self.close_material = state.get('close_material', '')
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
        if self.render_style == '近景摄影' or reflection.KEY in values:
            saved = values.get(reflection.KEY)
            self.values[reflection.KEY] = saved if isinstance(saved, str) and saved.strip() else reflection.OPTIONS[0]
            self.locks[reflection.KEY] = state.get('locks', {}).get(reflection.KEY) is True
            self.hidden[reflection.KEY] = state.get('hidden', {}).get(reflection.KEY) is True
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
        if not self.prompt or self.prompt == self.rendered:
            self.regenerate()

    def active_profile(self):
        return scene_profile(self.profile, self.render_style)

    def active_pools(self):
        if self.render_style == '近景摄影':
            from scene_tool.config.close_dimensions import upgrade_options
            return {d['key']: upgrade_options(d.get('close_key', d['key']), self.closeup_pools.get(d['key'], d['options'])) for d in self.active_profile()['dimensions']}
        if self.render_style != COMMERCIAL:
            return self.pools
        pools = {d['key']: list(d['options']) for d in self.active_profile()['dimensions']}
        for key, items in self.commercial_pools.items():
            if key in pools and isinstance(items, list) and len(items) >= 2:
                pools[key] = items
        return pools

    def camera_pool(self):
        return camera_pool(self.pools['camera'], self.profile['environment'], self.render_style)

    def studio_draw(self, *, keep=False, fixed_camera=False, fixed_key=None, preserve_values=False):
        from scene_tool.generation.studio_shots import draw_shot
        dims = self.active_profile()['dimensions']
        mapping = {d['key']:d.get('close_key', d['key']) for d in dims}
        pools = {mapping[k]:v for k,v in self.active_pools().items()}
        pools['camera'] = self.camera_pool()
        locks = {mapping[k] for k in self.locks if self.locks[k]}
        # Scene slots also serve buyer/commercial fields. A lock on a value
        # from that other schema must not inject a venue/activity into a studio shot.
        other = scene_profile(self.profile, COMMERCIAL)['dimensions']
        for d in other:
            key = d['key']
            value = self.values[key]
            if value not in pools[mapping[key]] and (value in self.pools[key] or value in d['options'] or value in self.commercial_pools.get(key, ())):
                locks.discard(mapping[key])
        if fixed_camera:
            locks.add('camera')
        if preserve_values:
            locks.update(mapping[k] for k,v in self.values.items() if v and k in mapping)
        if fixed_key:
            locks.add(mapping[fixed_key])
        values, choices = draw_shot({v:self.values.get(k, '') for k,v in mapping.items()}, locks, pools,
                                    self.rng, self.bags, keep=keep)
        self.hidden.setdefault(reflection.KEY, False)
        self.locks.setdefault(reflection.KEY, False)
        self.values.update({k:values[v] for k,v in mapping.items()})
        return {k:choices[v] for k,v in mapping.items()}

    def draw(self, *, preserve_locked=False):
        if self.render_style == '近景摄影':
            self.studio_draw()
            return
        for key, pool in self.active_pools().items():
            if preserve_locked and self.locks[key] and self.values[key].strip():
                continue
            if key == 'camera':
                self.values[key] = draw_camera(self.camera_pool(), self.values[key], self.locks[key], self.bags, self.rng)
                continue
            if self.render_style in (COMMERCIAL, '近景摄影'):
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
        return make_scene_prompt(self.active_profile(), dict(self.values, close_subject=self.close_subject, close_material=self.close_material), self.extra, self.hidden, self.render_style, self.product_size)

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
        return {key: getattr(self, key) for key in ('random_strategy', 'strategy_step', 'values', 'locks', 'hidden', 'render_style', 'product_size', 'close_subject', 'close_material', 'commercial_pools', 'closeup_pools', 'pools', 'bags', 'extra', 'prompt', 'rendered')}


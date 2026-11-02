import random
import unittest
from unittest.mock import patch, Mock
from types import SimpleNamespace

from scene_tool.config import highlight_position as pos, surface_reflection as surf
from scene_tool.config.closeup import CLOSEUP
from scene_tool.config.paths import RESOURCES
from scene_tool.domain.prompts import make_prompt
from scene_tool.domain.scene_model import SceneModel
from scene_tool.generation.parameters import Randomizer
from scene_tool.storage.pools import load_pools
from scene_tool.storage.scenes import load_profiles
from scene_tool.ui.highlight_binding import bind_highlight


class Var:
    def __init__(self, value): self.value = value
    def get(self): return self.value
    def set(self, value): self.value = value


class HighlightLinkTests(unittest.TestCase):
    def setUp(self):
        self.engine = Randomizer(load_pools(RESOURCES/'pools.json'), random.Random(8))

    def test_manual_dropdown_controls_both_fields_and_conflict_rolls_back(self):
        values = self.engine.draw({surf.KEY:surf.MATTE}, [surf.KEY], render_style=CLOSEUP)
        view = SimpleNamespace(render_style=Var(CLOSEUP), industry=Var('美业'), engine=self.engine,
                               values={k:Var(v) for k,v in values.items()}, locks={k:Var(False) for k in values},
                               combos={k:Mock() for k in values}, studio_values=values)
        view.current = lambda: {k:v.get() for k,v in view.values.items()}
        def choose(key, value):
            bind_highlight(view, key)
            view.values[key].set(value)
            event, callback = view.combos[key].bind.call_args_list[0].args
            self.assertEqual(event, '<<ComboboxSelected>>')
            callback(None)
        self.assertEqual(values[pos.KEY], pos.NONE)
        choose(pos.KEY, pos.SIDES)
        self.assertEqual(view.values[surf.KEY].get(), surf.GLOSS)
        choose(surf.KEY, surf.MATTE)
        self.assertEqual(view.values[pos.KEY].get(), pos.NONE)
        view.locks[surf.KEY].set(True)
        with patch('scene_tool.ui.highlight_binding.messagebox.showwarning') as warning:
            choose(pos.KEY, pos.CENTER)
            warning.assert_called_once()
        self.assertEqual(view.values[pos.KEY].get(), pos.NONE)
        self.assertEqual(view.values[surf.KEY].get(), surf.MATTE)

    def test_random_draws_never_contradict_and_hidden_fields_do_not_leak(self):
        values = {}
        seen = set()
        for _ in range(60):
            values = self.engine.draw(values, render_style=CLOSEUP)
            seen.add(values[pos.KEY])
            self.assertTrue(pos.compatible(values[surf.KEY], values[pos.KEY]))
        self.assertEqual(seen, set(pos.OPTIONS))
        for where in (pos.CENTER, pos.SIDES):
            values.update({surf.KEY:surf.HIGH, pos.KEY:where})
            values = self.engine.draw(values, [surf.KEY,pos.KEY], render_style=CLOSEUP)
            prompt = make_prompt(values, render_style=CLOSEUP)
            self.assertIn(pos.prompt_value(where), prompt)
            self.assertNotIn('压低镜面眩光', prompt)
            self.assertNotIn(where, make_prompt(values, hidden=[pos.KEY], render_style=CLOSEUP))
            self.assertNotIn('表面反光：', make_prompt(values, hidden=[surf.KEY], render_style=CLOSEUP))

    def test_seven_scenes_accept_edits_and_migrate_old_locks(self):
        old = '宽幅柔光：在材质能反光的区域保留宽而柔和的亮带'
        for profile in load_profiles():
            model = SceneModel(profile, {'render_style':CLOSEUP})
            lk = next(d['key'] for d in model.active_profile()['dimensions'] if d.get('close_key') == pos.KEY)
            model.values.update({lk:pos.LEGACY[1], surf.KEY:old})
            model.locks[lk] = model.locks[surf.KEY] = True
            model.draw()
            self.assertEqual(model.values[surf.KEY], surf.GLOSS)
            self.assertEqual(model.values[lk], pos.CENTER)
            self.assertNotIn('宽幅柔光', model.generate())
            model.locks[lk] = model.locks[surf.KEY] = False
            model.values[surf.KEY] = surf.MATTE
            model.studio_draw(keep=True, fixed_key=surf.KEY)
            self.assertEqual(model.values[lk], pos.NONE)
            model.values[lk] = pos.SIDES
            model.studio_draw(keep=True, fixed_key=lk)
            self.assertEqual(model.values[surf.KEY], surf.GLOSS)
            self.assertIn(pos.prompt_value(pos.SIDES), model.generate())

"""Commercial intent is reversible and persists through the real scene codec."""
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scene_tool.config.render_styles import BUYER, COMMERCIAL
from scene_tool.config.telephoto import TELEPHOTO_ANGLES
from scene_tool.config.defaults import DIMENSIONS
from scene_tool.domain.industry_profiles import EXTRA_DIMENSIONS
from scene_tool.domain.prompts import make_prompt
from scene_tool.domain.scene_model import SceneModel
from scene_tool.domain.prompt_migration import migrate_prompt_state
from scene_tool.storage.scenes import load_profiles
from scene_tool.storage.scene_sessions import save_states, load_states
from scene_tool.ui.render_style_binding import RenderStyleSelector


class Var:
    def __init__(self, value): self.value = value
    def get(self): return self.value
    def set(self, value): self.value = value


class RenderStyleTests(unittest.TestCase):
    def test_opening_style_roundtrip_preserves_camera_and_removes_buyer_rules(self):
        values = {k: '示例值' for k, _ in (*DIMENSIONS, *EXTRA_DIMENSIONS)}
        values['camera'] = TELEPHOTO_ANGLES[2]
        before = make_prompt(values)
        commercial = make_prompt(values, render_style=COMMERCIAL)
        self.assertIn('商业效果图要求', commercial)
        self.assertIn('等效100mm', commercial)
        for word in ('未经精修', '随手拍下', '手持手机', '不要3D渲染', '生活化细节：', '路人（0—3人）'):
            self.assertNotIn(word, commercial)
        self.assertEqual(before, make_prompt(values, render_style=BUYER))
        self.assertEqual(values['camera'], TELEPHOTO_ANGLES[2])

    def test_all_scene_styles_persist_without_changing_random_state(self):
        for profile in load_profiles():
            model = SceneModel(profile)
            model.values['camera'] = TELEPHOTO_ANGLES[-1]
            model.locks['camera'] = True
            model.hidden['ratio'] = True
            before = model.state().copy()
            model.render_style = COMMERCIAL
            model.regenerate()
            self.assertIn('等效150mm', model.prompt)
            self.assertNotIn('手持手机', model.prompt)
            with tempfile.TemporaryDirectory() as tmp:
                save_states(Path(tmp), profile['name'], {profile['name']: model})
                saved = load_states(Path(tmp), [profile])['scenes'][profile['name']]
                restored = SceneModel(profile, saved)
                self.assertEqual(restored.render_style, COMMERCIAL)
                restored.render_style = BUYER
                restored.regenerate()
                self.assertIn('未经精修', restored.prompt)
                for key in ('values', 'locks', 'hidden', 'bags', 'pools'):
                    self.assertEqual(restored.state()[key], before[key])

    def test_hidden_camera_and_custom_constraints(self):
        values = {k: '示例值' for k, _ in (*DIMENSIONS, *EXTRA_DIMENSIONS)}
        values['camera'] = TELEPHOTO_ANGLES[0]
        prompt = make_prompt(values, constraints='我的自定义要求', hidden={'camera'}, render_style=COMMERCIAL)
        self.assertNotIn('75', prompt)
        self.assertIn('我的自定义要求', prompt)

    def test_opening_migration_retains_commercial_style(self):
        values = {k: '示例值' for k, _ in (*DIMENSIONS, *EXTRA_DIMENSIONS)}
        state = dict(values=values, render_style=COMMERCIAL, prompt='old', rendered='old')
        self.assertIn('商业效果图要求', migrate_prompt_state(state, ())['prompt'])

    def test_cancel_style_change_keeps_manual_text_and_previous_style(self):
        view = SimpleNamespace(render_style=Var(BUYER), refresh=lambda **_: False)
        selector = RenderStyleSelector.__new__(RenderStyleSelector)
        selector.switcher = SimpleNamespace(active='开业场景', window=view)
        selector.value = Var(COMMERCIAL)
        selector.change()
        self.assertEqual(view.render_style.get(), BUYER)
        self.assertEqual(selector.value.get(), BUYER)

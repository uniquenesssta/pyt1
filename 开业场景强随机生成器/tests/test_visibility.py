"""Visibility must affect generated/exported text without changing random values."""
import sys
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scene_tool.config.defaults import DIMENSIONS
from scene_tool.domain.prompts import make_prompt
from scene_tool.domain.scene_model import SceneModel
from scene_tool.storage.scenes import load_profiles
from scene_tool.storage.scene_sessions import save_states, load_states
from scene_tool.domain.prompt_migration import migrate_prompt_state
from scene_tool.ui.visibility_binding import change_opening, change_scene


class Var:
    def __init__(self, value): self.value = value
    def get(self): return self.value
    def set(self, value): self.value = value


class VisibilityTests(unittest.TestCase):
    def test_each_opening_field_is_omitted_and_restored(self):
        values = {k: f'唯一值_{k}' for k, _ in DIMENSIONS}
        for key, label in DIMENSIONS:
            prompt = make_prompt(values, hidden={key})
            self.assertNotIn(values[key], prompt)
            self.assertIn(values[key], make_prompt(values))
        self.assertNotIn('专属开业文案', make_prompt(values, copy='专属开业文案', hidden={'copy'}))
        self.assertNotIn('场地要求：', make_prompt(values, hidden={'environment'}))

    def test_all_scene_fields_hidden_roundtrip_and_locks_independent(self):
        for profile in load_profiles():
            model = SceneModel(profile)
            for key in model.values:
                model.values[key] = f'唯一值_{key}'
                model.hidden[key] = True
                model.locks[key] = True
            model.regenerate()
            self.assertNotIn('唯一值_', model.prompt)
            before = dict(model.values)
            model.draw()
            self.assertEqual(model.values, before)
            with tempfile.TemporaryDirectory() as tmp:
                save_states(Path(tmp), profile['name'], {profile['name']: model})
                state = load_states(Path(tmp), [profile])['scenes'][profile['name']]
                loaded = SceneModel(profile, state)
                self.assertEqual(loaded.hidden, model.hidden)
                loaded.hidden['camera'] = False
                self.assertIn('唯一值_camera', loaded.generate())

    def test_old_generated_session_migration_keeps_hidden_fields_out(self):
        values = {k: f'值_{k}' for k, _ in DIMENSIONS}
        state = dict(values=values, hidden={'brand': True}, prompt='旧文', rendered='旧文')
        migrated = migrate_prompt_state(state, ())
        self.assertNotIn('值_brand', migrated['prompt'])
        self.assertIn('值_address', migrated['prompt'])

    def test_cancel_manual_prompt_replacement_rolls_back_checkbox(self):
        variable = Var(True)
        view = SimpleNamespace(hidden={'camera': variable}, refresh=lambda **_: False)
        change_opening(view, 'camera')
        self.assertFalse(variable.get())
        variable.set(True)
        captures = []
        panel = SimpleNamespace(hidden={'camera': variable}, allow_replace=lambda: False,
                                capture=lambda: captures.append(variable.get()))
        change_scene(panel, 'camera')
        self.assertEqual(captures, [False])

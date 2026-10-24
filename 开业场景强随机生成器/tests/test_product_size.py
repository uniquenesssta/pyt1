"""Product shape/size is independent of photo ratio and random selection."""
import sys
import tempfile
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scene_tool.config.defaults import DIMENSIONS
from scene_tool.config.product_size import FOLLOW_REFERENCE, FIXED_LARGE
from scene_tool.config.render_styles import BUYER, COMMERCIAL
from scene_tool.domain.prompts import make_prompt
from scene_tool.domain.scene_model import SceneModel
from scene_tool.storage.scenes import load_profiles
from scene_tool.storage.scene_sessions import save_states, load_states
from scene_tool.domain.prompt_migration import migrate_prompt_state


class ProductSizeTests(unittest.TestCase):
    def setUp(self):
        self.values = {k: '示例值' for k, _ in DIMENSIONS}
        self.values.update(environment='室内', ratio='16:9')

    def test_reference_mode_removes_old_large_board_rule_in_both_styles(self):
        for style in (BUYER, COMMERCIAL):
            prompt = make_prompt(self.values, render_style=style, product_size=FOLLOW_REFERENCE)
            self.assertNotIn('3.5', prompt)
            self.assertNotIn('完整大板', prompt)
            self.assertIn('不把参考照片的画幅当成产品比例', prompt)
            self.assertIn('画面比例：16:9', prompt)
            self.assertIn('不凭照片编造米数', prompt)

    def test_fixed_and_custom_sizes_are_separate_from_photo_ratio(self):
        fixed = make_prompt(self.values, product_size=FIXED_LARGE)
        self.assertIn('3.5米宽、2.2米高', fixed)
        for size in ('宽2米×高1.5米', '固定比例：1:1'):
            prompt = make_prompt(self.values, product_size=size)
            self.assertIn(size, prompt)
            self.assertNotIn('3.5', prompt)
            self.assertIn('画面比例：16:9', prompt)

    def test_scene_spec_persists_and_random_draw_does_not_change_it(self):
        for profile in load_profiles():
            model = SceneModel(profile)
            self.assertEqual(model.product_size, FOLLOW_REFERENCE)
            model.product_size = '宽2米×高1.5米'
            model.draw()
            model.regenerate()
            self.assertIn(model.product_size, model.prompt)
            with tempfile.TemporaryDirectory() as tmp:
                save_states(Path(tmp), profile['name'], {profile['name']: model})
                saved = load_states(Path(tmp), [profile])['scenes'][profile['name']]
                restored = SceneModel(profile, saved)
                self.assertEqual(restored.product_size, model.product_size)

    def test_legacy_opening_fixed_size_and_new_reference_choice_migrate(self):
        state = dict(values=self.values, prompt='old', rendered='old')
        self.assertIn('3.5米宽', migrate_prompt_state(state, ())['prompt'])
        state['product_size'] = FOLLOW_REFERENCE
        self.assertNotIn('3.5', migrate_prompt_state(state, ())['prompt'])

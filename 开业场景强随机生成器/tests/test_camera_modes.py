"""Exercise mode priority, locks, exhaustion and persisted shuffle progress."""
import random
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from scene_tool.config.camera_modes import COMMERCIAL_ANGLES, INDOOR_ANGLES
from scene_tool.config.render_styles import BUYER, COMMERCIAL
from scene_tool.config.product_size import normalize_size, FOLLOW_REFERENCE, PRODUCT_SIZE_CHOICES
from scene_tool.generation.parameters import Randomizer
from scene_tool.storage.pools import load_pools
from scene_tool.storage.scenes import load_profiles
from scene_tool.storage.scene_codec import encode_scene, decode_scene
from scene_tool.domain.scene_model import SceneModel
from scene_tool.ui.components.product_size import product_size_row


class CameraModeTests(unittest.TestCase):
    def test_locked_environment_and_commercial_priority(self):
        pools = load_pools(Path(__file__).resolve().parents[1] / 'resources/pools.json')
        for environment in ('室内', '室外'):
            for style in (BUYER, COMMERCIAL):
                engine = Randomizer(pools, random.Random(29), generated=False)
                expected = list(COMMERCIAL_ANGLES if style == COMMERCIAL else INDOOR_ANGLES if environment == '室内' else pools['camera'])
                current = {'environment': environment}
                seen = []
                for _ in expected:
                    current = engine.draw(current, ['environment'], render_style=style)
                    self.assertEqual(current['environment'], environment)
                    seen.append(current['camera'])
                self.assertEqual(set(seen), set(expected))
                self.assertEqual(len(seen), len(set(seen)))
                locked = engine.draw(current, ['environment', 'camera'], render_style=style)
                self.assertEqual(locked['camera'], current['camera'])

    def test_incompatible_camera_lock_is_reconciled_on_mode_change(self):
        engine = Randomizer(load_pools(Path(__file__).resolve().parents[1] / 'resources/pools.json'))
        values = engine.draw({'environment': '室内'}, ['environment'])
        values = engine.draw(values, ['environment', 'camera'], render_style=COMMERCIAL)
        self.assertIn(values['camera'], COMMERCIAL_ANGLES)
        values = engine.draw(values, ['environment', 'camera'], render_style=BUYER)
        self.assertIn(values['camera'], INDOOR_ANGLES)

    def test_all_scenes_use_commercial_pool_and_persist_remaining_bag(self):
        for profile in load_profiles():
            model = SceneModel(profile)
            model.render_style = COMMERCIAL
            for _ in range(7): model.draw()
            model.regenerate()
            restored = SceneModel(profile, decode_scene(profile, encode_scene(model)))
            self.assertEqual(restored.bags['camera_mode:commercial'], model.bags['camera_mode:commercial'])
            seen = {model.values['camera']}
            for _ in range(35):
                restored.draw()
                value = restored.values['camera']
                self.assertIn(value, COMMERCIAL_ANGLES)
                self.assertNotIn(value, seen)
                seen.add(value)
            self.assertNotIn('后置主摄1倍', restored.generate())

    def test_size_presets_are_dimensions_and_custom_button_is_visible(self):
        self.assertTrue(all('比例' not in x for x in PRODUCT_SIZE_CHOICES))
        self.assertEqual(normalize_size('跟随参考图产品比例'), FOLLOW_REFERENCE)
        self.assertEqual(normalize_size('固定比例：1:1'), FOLLOW_REFERENCE)
        variable = MagicMock()
        variable.get.return_value = FOLLOW_REFERENCE
        results = MagicMock()
        with patch('scene_tool.ui.components.product_size.ttk.Button') as button, patch('scene_tool.ui.components.product_size.simpledialog.askstring', return_value='宽2米×高1米'):
            product_size_row(results, variable)
            self.assertEqual(results.result.call_args.args[0], '产品尺寸')
            self.assertEqual(button.call_args.kwargs['text'], '自己填尺寸')
            button.return_value.pack.assert_called_once()
            button.call_args.kwargs['command']()
            variable.set.assert_called_with('宽2米×高1米')

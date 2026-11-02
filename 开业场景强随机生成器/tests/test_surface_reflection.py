"""Reflection is a separate controllable studio dimension across all scenes."""
import random
import unittest

from scene_tool.config import surface_reflection as refl
from scene_tool.config.closeup import CLOSEUP
from scene_tool.config.paths import RESOURCES
from scene_tool.config.render_styles import BUYER, COMMERCIAL
from scene_tool.config.studio_shots import SHOTS, camera_family
from scene_tool.domain.prompts import make_prompt
from scene_tool.domain.scene_model import SceneModel
from scene_tool.generation.parameters import Randomizer
from scene_tool.storage.pools import load_pools
from scene_tool.storage.scenes import load_profiles
from scene_tool.storage.scene_codec import encode_scene, decode_scene


class ReflectionTests(unittest.TestCase):
    def test_opening_independent_random_and_locked_manual_selection(self):
        engine = Randomizer(load_pools(RESOURCES/'pools.json'), random.Random(7))
        current = {'close_material':'写真布背胶'}
        for family in SHOTS.values():
            current['camera'] = family['camera'][0]
            seen = set()
            for _ in refl.OPTIONS:
                current = engine.draw(current, ['camera'], render_style=CLOSEUP)
                seen.add(current[refl.KEY])
            self.assertEqual(seen, set(refl.OPTIONS))
        current[refl.KEY] = '仅一侧有轻微柔光'
        families = set()
        for _ in range(3):
            current = engine.draw(current, [refl.KEY], render_style=CLOSEUP)
            families.add(camera_family(current['camera']))
            self.assertIn('表面反光：仅一侧有轻微柔光', make_prompt(current, render_style=CLOSEUP))
            self.assertNotIn('仅一侧有轻微柔光', make_prompt(current, render_style=CLOSEUP, hidden=[refl.KEY]))
            self.assertEqual(current['close_material'], '写真布背胶')
        self.assertEqual(families, set(SHOTS))

    def test_scene_save_restore_and_style_roundtrip(self):
        for profile in load_profiles():
            model = SceneModel(profile, {'render_style': CLOSEUP, 'close_material':'写真布背胶'})
            model.values[refl.KEY] = refl.OPTIONS[2]
            model.locks[refl.KEY] = True
            model.hidden[refl.KEY] = True
            saved = decode_scene(profile, encode_scene(model))
            model = SceneModel(profile, saved)
            model.draw()
            self.assertEqual(model.values[refl.KEY], refl.OPTIONS[2])
            self.assertTrue(model.locks[refl.KEY])
            self.assertNotIn(refl.LABEL + '：', model.generate())
            model.hidden[refl.KEY] = False
            self.assertIn(refl.LABEL + '：' + refl.OPTIONS[2], model.generate())
            for style in (BUYER, COMMERCIAL):
                model.render_style = style
                model.draw()
                self.assertNotIn(refl.LABEL + '：', model.generate())
            model.render_style = CLOSEUP
            model.draw()
            self.assertIn(refl.LABEL + '：' + refl.OPTIONS[2], model.generate())

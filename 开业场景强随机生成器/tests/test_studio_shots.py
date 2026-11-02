import random
import unittest
from copy import deepcopy

from scene_tool.config.closeup import CLOSEUP, LEGACY_ANGLES
from scene_tool.config.studio_shots import FLAT, ALONG, CORNER, SHOTS, camera_family
from scene_tool.config.paths import RESOURCES
from scene_tool.domain.prompts import make_prompt
from scene_tool.domain.scene_model import SceneModel
from scene_tool.generation.parameters import Randomizer
from scene_tool.generation.studio_shots import ShotConflict
from scene_tool.storage.pools import load_pools
from scene_tool.storage.scenes import load_profiles
from scene_tool.storage.scene_codec import encode_scene, decode_scene


class StudioShotsTests(unittest.TestCase):
    def setUp(self):
        self.engine = Randomizer(load_pools(RESOURCES/'pools.json'), random.Random(26))

    def check_family(self, values, text):
        name = camera_family(values['camera'])
        self.assertIn('本轮棚拍镜头：' + name, text)
        self.assertNotIn('拍摄地点：', text)
        self.assertNotIn('室内 / 室外：', text)
        for key, allowed in SHOTS[name].items():
            if key in values:
                self.assertIn(values[key], allowed)
                self.assertIn(values[key], text)
        return name

    def test_opening_strong_rounds_cover_three_coherent_shots(self):
        current = {'close_subject':'对联', 'close_material':'写真布背胶', 'environment':'室外'}
        for _ in range(8):
            families = set()
            for _ in range(3):
                current = self.engine.draw(current, render_style=CLOSEUP)
                text = make_prompt(current, render_style=CLOSEUP)
                families.add(self.check_family(current, text))
                self.assertIn('单幅绝不复制', text)
                self.assertIn('写真布背胶', text)
            self.assertEqual(families, set(SHOTS))
        self.assertEqual(current['environment'], '室外')  # preserved for the buyer mode

    def test_locked_camera_and_locked_field_constrain_family(self):
        for key in ('camera', 'detail_crop', 'detail_focus', 'detail_plane'):
            val = SHOTS[ALONG][key][0]
            current = {key: val}
            for _ in range(6):
                current = self.engine.draw(current, [key], strong=False, render_style=CLOSEUP)
                self.assertEqual(current[key], val)
                self.assertEqual(camera_family(current['camera']), ALONG)

    def test_conflict_is_atomic_and_custom_pool_is_respected(self):
        current = {'camera':SHOTS[FLAT]['camera'][0], 'detail_crop':SHOTS[ALONG]['detail_crop'][0]}
        bags = deepcopy(self.engine.bags)
        with self.assertRaises(ShotConflict):
            self.engine.draw(current, list(current), render_style=CLOSEUP)
        self.assertEqual(self.engine.bags, bags)
        self.engine.industry_overrides = {'通用|室外|' + CLOSEUP: {'detail_light':['左侧自定义柔光','右侧自定义柔光']}}
        current = self.engine.draw(current, ['camera'], render_style=CLOSEUP)
        self.assertIn(current['detail_light'], ('左侧自定义柔光','右侧自定义柔光'))

    def test_sync_preserves_camera_family_and_does_not_consume_bag(self):
        current = self.engine.draw({}, render_style=CLOSEUP)
        current['camera'] = SHOTS[CORNER]['camera'][1]
        values, _ = self.engine.studio_draw(current, ['camera'], '美业', keep=True)
        self.check_family(values, make_prompt(values, render_style=CLOSEUP))
        before = deepcopy(self.engine.bags)
        again, _ = self.engine.studio_draw(values, [], '美业', keep=True)
        self.assertEqual(values, again)
        self.assertEqual(before, self.engine.bags)

    def test_seven_scenes_draw_resume_and_hidden_camera(self):
        for profile in load_profiles():
            model = SceneModel(profile, {'render_style':CLOSEUP, 'close_material':'涂布纸'}, rng=random.Random(45))
            for _ in range(2):
                model.draw()
                mapped = {d.get('close_key', d['key']):model.values[d['key']] for d in model.active_profile()['dimensions']}
                self.check_family(mapped, model.generate())
            saved = decode_scene(profile, encode_scene(model))
            restored = SceneModel(profile, saved)
            self.assertEqual(restored.bags, model.bags)
            restored.hidden['camera'] = True
            self.assertNotIn('本轮棚拍镜头：', restored.generate())
            self.assertNotIn(restored.values['camera'], restored.generate())

    def test_old_locked_low_view_migrates_to_along_family(self):
        values = self.engine.draw({'camera':LEGACY_ANGLES[7]}, ['camera'], render_style=CLOSEUP)
        self.assertEqual(camera_family(values['camera']), ALONG)

"""New camera defaults migrate safely and do not conflict with 1x rules."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scene_tool.config.telephoto import TELEPHOTO_ANGLES
from scene_tool.config.paths import RESOURCES
from scene_tool.storage.pools import load_startup_pools
from scene_tool.storage.scenes import load_profiles
from scene_tool.domain.scene_model import SceneModel
from scene_tool.domain.prompts import make_prompt
from scene_tool.config.defaults import DIMENSIONS


class TelephotoTests(unittest.TestCase):
    def test_focal_presets_in_all_scenes_and_no_1x_conflict(self):
        for profile in load_profiles():
            model = SceneModel(profile)
            for camera in TELEPHOTO_ANGLES:
                self.assertIn(camera, model.pools['camera'])
                model.values['camera'] = camera
                prompt = model.generate()
                self.assertIn(camera, prompt)
                self.assertNotIn('1倍', prompt)
                self.assertNotIn('后置主摄', prompt)
                model.hidden['camera'] = True
                self.assertNotIn(camera, model.generate())
                self.assertNotIn('本轮指定的等效焦段', model.generate())
                model.hidden['camera'] = False
        values = {k: '默认值' for k, _ in DIMENSIONS}
        values['camera'] = TELEPHOTO_ANGLES[-1]
        self.assertNotIn('1倍', make_prompt(values))

    def test_old_opening_pool_upgrades_custom_camera_stays(self):
        original = json.loads((RESOURCES / 'legacy_pools_v4.json').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'pools.json'
            path.write_text(json.dumps(original))
            pools, errors = load_startup_pools(path)
            self.assertFalse(errors)
            self.assertTrue(set(TELEPHOTO_ANGLES) <= set(pools['camera']))
            original['camera'] = ['我的角度1', '我的角度2']
            path.write_text(json.dumps(original))
            pools, _ = load_startup_pools(path)
            self.assertEqual(pools['camera'], original['camera'])

    def test_old_scene_override_is_upgraded(self):
        for profile in load_profiles():
            model = SceneModel(profile, {'pools': {'camera': profile['legacy_camera']}})
            self.assertTrue(set(TELEPHOTO_ANGLES) <= set(model.pools['camera']))

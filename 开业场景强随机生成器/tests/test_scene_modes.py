import json
import random
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scene_tool.storage.scenes import load_profiles
from scene_tool.domain.scene_model import SceneModel


class SceneModeTests(unittest.TestCase):
    def setUp(self):
        self.profiles = load_profiles()

    def test_seven_distinct_schemas_and_valid_candidates(self):
        self.assertEqual(len(self.profiles), 7)
        schemas = []
        for profile in self.profiles:
            dimensions = profile['dimensions']
            self.assertEqual(len(dimensions), 10)
            self.assertEqual(len({d['key'] for d in dimensions}), 10)
            schemas.append(tuple(d['label'] for d in dimensions))
            for dim in dimensions:
                self.assertGreaterEqual(len(dim['options']), 4)
                self.assertEqual(len(dim['options']), len(set(dim['options'])))
        self.assertEqual(len(set(schemas)), 7)

    def test_every_scene_has_independent_nonrepeating_bags(self):
        for profile in self.profiles:
            model = SceneModel(profile, rng=random.Random(42))
            seen = {key: [value] for key, value in model.values.items()}
            for _ in range(100):
                old = dict(model.values)
                model.draw()
                for key, value in model.values.items():
                    self.assertNotEqual(value, old[key])
                    self.assertIn(value, model.pools[key])
                    if len(seen[key]) < len(model.pools[key]):
                        seen[key].append(value)
            for key in seen:
                self.assertEqual(set(seen[key]), set(model.pools[key]))

    def test_locks_edits_and_pools_survive_roundtrip(self):
        for profile in self.profiles:
            model = SceneModel(profile)
            key = profile['dimensions'][0]['key']
            model.values[key] = '我的指定风格'
            model.locks[key] = True
            model.set_pool('camera', ['我的左侧视角', '我的右侧视角'])
            model.prompt = '手动修改的整段提示词'
            model.extra = '保留参考图姓名'
            loaded = SceneModel(profile, json.loads(json.dumps(model.state())))
            loaded.draw()
            self.assertEqual(loaded.values[key], '我的指定风格')
            self.assertEqual(loaded.prompt, '手动修改的整段提示词')
            self.assertEqual(loaded.extra, model.extra)
            self.assertEqual(loaded.pools['camera'], model.pools['camera'])

    def test_scene_text_has_own_boundaries_without_commercial_dimensions(self):
        for profile in self.profiles:
            model = SceneModel(profile)
            prompt = model.generate()
            self.assertIn(profile['name'], prompt)
            self.assertIn(profile['rules'], prompt)
            self.assertNotIn('3.5米宽', prompt)
            self.assertNotIn('品牌名称：', prompt)
            self.assertNotIn('街道地址：', prompt)
            self.assertNotIn('Logo 图形形态：', prompt)
            self.assertIn('不添加实体花艺', prompt)
            if profile['environment'] == '室内':
                self.assertIn('不出现室内车辆', prompt)

    def test_reset_undo_and_scene_isolation(self):
        a, b = [SceneModel(p) for p in self.profiles[:2]]
        original_b = json.dumps(b.state(), ensure_ascii=False)
        a.extra, a.prompt = '补充', '我的手改提示词'
        a.reset()
        self.assertEqual(a.extra, '')
        a.undo_reset()
        self.assertEqual(a.prompt, '我的手改提示词')
        self.assertEqual(a.extra, '补充')
        a.draw()
        self.assertEqual(json.dumps(b.state(), ensure_ascii=False), original_b)

    def test_invalid_pool_rejected_without_replacing_old_pool(self):
        model = SceneModel(self.profiles[0])
        original = list(model.pools['camera'])
        with self.assertRaises(ValueError):
            model.set_pool('camera', ['只有一项', '只有一项'])
        self.assertEqual(model.pools['camera'], original)

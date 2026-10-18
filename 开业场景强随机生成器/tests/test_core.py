import json
from pathlib import Path
import random
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scene_tool.config.defaults import DIMENSIONS
from scene_tool.generation.parameters import Randomizer
from scene_tool.storage.pools import load_pools
from scene_tool.domain.prompts import make_prompt
from scene_tool.storage.json_files import atomic_json
from scene_tool.domain.pools import validate_pools, upgrade_pools
from scene_tool.generation.brands import generate_brand, brand_from_parts
from scene_tool.config.vocabulary import SYLLABLES


class RandomizerTests(unittest.TestCase):
    def setUp(self):
        self.pools = load_pools(Path(__file__).resolve().parents[1] / 'resources' / 'pools.json')
        self.engine = Randomizer(self.pools, random.Random(333), generated=False)

    def test_twelve_independent_dimensions(self):
        self.assertEqual(len(DIMENSIONS), 12)
        pools = {key: ['a', 'b', 'c', 'd'] for key, _ in DIMENSIONS}
        values = Randomizer(pools, random.Random(333), generated=False).draw()
        self.assertGreater(len(set(values.values())), 1)

    def test_strong_no_immediate_repeats_over_many_cycles(self):
        previous = self.engine.draw()
        for _ in range(1000):
            current = self.engine.draw(previous)
            for key, _ in DIMENSIONS:
                self.assertNotEqual(current[key], previous[key])
                pool_key = {'architecture': 'interior', 'placement': 'indoor_placement', 'balloons': 'indoor_balloons'}.get(key, key) if current['environment'] == '室内' else key
                self.assertIn(current[key], self.pools[pool_key])
            previous = current

    def test_each_dimension_exhausts_pool_before_repeating(self):
        previous = {}
        seen = {key: [] for key in self.pools}
        for _ in range(400):
            previous = self.engine.draw(previous)
            for key, _ in DIMENSIONS:
                pool_key = {'architecture': 'interior', 'placement': 'indoor_placement', 'balloons': 'indoor_balloons'}.get(key, key) if previous['environment'] == '室内' else key
                if len(seen[pool_key]) < len(self.pools[pool_key]):
                    seen[pool_key].append(previous[key])
        for key in self.pools:
            self.assertEqual(set(seen[key]), set(self.pools[key]))
            self.assertEqual(len(seen[key]), len(set(seen[key])))

    def test_lock_preserves_custom_value_and_bag(self):
        previous = self.engine.draw()
        previous['brand'] = '我的品牌'
        bag = list(self.engine.bags['brand'])
        current = self.engine.draw(previous, ['brand'])
        self.assertEqual(current['brand'], '我的品牌')
        self.assertEqual(self.engine.bags['brand'], bag)
        self.assertNotEqual(current['camera'], previous['camera'])

    def test_all_locked_no_mutation(self):
        previous = self.engine.draw()
        self.assertEqual(previous, self.engine.draw(previous, previous.keys()))

    def test_standard_no_immediate_repeat(self):
        previous = self.engine.draw()
        for _ in range(50):
            current = self.engine.draw(previous, strong=False)
            self.assertTrue(all(current[k] != previous[k] for k in previous))
            previous = current

    def test_resume_bags_and_reject_bad_entries(self):
        self.engine.draw()
        restored = Randomizer(self.pools)
        restored.restore_bags(self.engine.bags)
        self.assertEqual(restored.bags, self.engine.bags)
        restored.restore_bags({'brand': [None, {}, 'LUMÉ 露米', 'LUMÉ 露米'], 'unknown': []})
        self.assertEqual(restored.bags['brand'], ['LUMÉ 露米'])

    def test_two_item_pool_and_manual_last_item(self):
        pools = {key: ['a', 'b'] for key, _ in DIMENSIONS}
        engine = Randomizer(pools, generated=False)
        current = engine.draw()
        for key in current:
            current[key] = engine.bags[key][0]
        next_values = engine.draw(current)
        self.assertTrue(all(next_values[k] != current[k] for k in current))

    def test_prompt_has_exact_parameters_and_fixed_constraints(self):
        values = self.engine.draw()
        values['environment'] = '室外'
        prompt = make_prompt(values, industry='咖啡', extra='不要行人')
        for key, label in DIMENSIONS:
            self.assertIn(f'{label}：{values[key]}', prompt)
        for text in ['3.5米宽', '2.2米高', '印刷背景图案', '略微通透', '本轮行业：咖啡', '不要行人']:
            self.assertIn(text, prompt)
        values['city'] = ''
        with self.assertRaises(ValueError):
            make_prompt(values)

    def test_generated_brands_have_paired_chinese_syllables(self):
        mapping = dict(SYLLABLES)
        rng = random.Random(48)
        for _ in range(1000):
            western, chinese = generate_brand(rng).split()
            parts = [western[i:i+2] for i in range(0, len(western), 2)]
            self.assertIn(len(parts), (2, 3))
            self.assertEqual(chinese, ''.join(mapping[x] for x in parts))
        self.assertEqual(brand_from_parts([('LU', '露'), ('MI', '米'), ('NA', '娜')]), 'LUMINA 露米娜')

    def test_generated_values_recent_history_and_locks(self):
        engine = Randomizer(self.pools, random.Random(333))
        values = {}
        seen = {'brand': [], 'address': []}
        for _ in range(1000):
            values = engine.draw(values)
            for key in seen:
                self.assertNotIn(values[key], seen[key][-200:])
                seen[key].append(values[key])
        history = {k: list(v) for k, v in engine.recent.items()}
        locked = engine.draw(values, ['brand', 'address'])
        self.assertEqual(locked['brand'], values['brand'])
        self.assertEqual(locked['address'], values['address'])
        self.assertEqual(history, engine.recent)
        restored = Randomizer(self.pools)
        restored.restore_recent(history)
        self.assertEqual(restored.recent, history)

    def test_old_default_upgrade_preserves_customization(self):
        legacy = {'city': ['旧城市1', '旧城市2']}
        pools = dict(self.pools, city=legacy['city'])
        self.assertEqual(upgrade_pools(pools, self.pools, legacy)['city'], self.pools['city'])
        pools['city'] = ['自选城市1', '自选城市2']
        self.assertEqual(upgrade_pools(pools, self.pools, legacy)['city'], pools['city'])

    def test_validation_and_atomic_utf8_roundtrip(self):
        broken = dict(self.pools, brand=['same', 'same'])
        with self.assertRaises(ValueError):
            validate_pools(broken)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'data' / 'state.json'
            atomic_json(path, {'提示词': 'ÉLAN 悦岚'})
            atomic_json(path, {'提示词': '中文'})
            self.assertEqual(json.loads(path.read_text(encoding='utf-8')), {'提示词': '中文'})
            self.assertEqual(len(list(path.parent.iterdir())), 1)


if __name__ == '__main__':
    unittest.main()

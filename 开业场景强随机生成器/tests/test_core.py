import json
from pathlib import Path
import random
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core import DIMENSIONS, Randomizer, load_pools, make_prompt, atomic_json, validate_pools


class RandomizerTests(unittest.TestCase):
    def setUp(self):
        self.pools = load_pools(Path(__file__).resolve().parents[1] / 'pools.json')
        self.engine = Randomizer(self.pools, random.Random(333))

    def test_eleven_independent_dimensions(self):
        self.assertEqual(len(DIMENSIONS), 11)
        pools = {key: ['a', 'b', 'c', 'd'] for key, _ in DIMENSIONS}
        values = Randomizer(pools, random.Random(333)).draw()
        self.assertGreater(len(set(values.values())), 1)

    def test_strong_no_immediate_repeats_over_many_cycles(self):
        previous = self.engine.draw()
        for _ in range(1000):
            current = self.engine.draw(previous)
            for key, _ in DIMENSIONS:
                self.assertNotEqual(current[key], previous[key])
                self.assertIn(current[key], self.pools[key])
            previous = current

    def test_each_dimension_exhausts_pool_before_repeating(self):
        previous = {}
        seen = {key: [] for key, _ in DIMENSIONS}
        for i in range(max(map(len, self.pools.values()))):
            previous = self.engine.draw(previous)
            for key, _ in DIMENSIONS:
                if i < len(self.pools[key]):
                    seen[key].append(previous[key])
        for key, _ in DIMENSIONS:
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
        engine = Randomizer(pools)
        current = engine.draw()
        for key in current:
            current[key] = engine.bags[key][0]
        next_values = engine.draw(current)
        self.assertTrue(all(next_values[k] != current[k] for k in current))

    def test_prompt_has_exact_parameters_and_fixed_constraints(self):
        values = self.engine.draw()
        prompt = make_prompt(values, industry='咖啡', extra='不要行人')
        for key, label in DIMENSIONS:
            self.assertIn(f'{label}：{values[key]}', prompt)
        for text in ['3.5米宽', '2.2米高', '紫色渐变', '略微通透', '本轮行业：咖啡', '不要行人']:
            self.assertIn(text, prompt)
        values['city'] = ''
        with self.assertRaises(ValueError):
            make_prompt(values)

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

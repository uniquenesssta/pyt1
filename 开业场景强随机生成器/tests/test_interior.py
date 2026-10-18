import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scene_tool.config.paths import RESOURCES
from scene_tool.config.interior_styles import INTERIOR_STYLES
from scene_tool.storage.pools import load_pools
from scene_tool.generation.parameters import Randomizer
from scene_tool.domain.prompts import make_prompt


class InteriorTests(unittest.TestCase):
    def setUp(self):
        self.engine = Randomizer(load_pools(RESOURCES / 'pools.json'))

    def test_locked_indoor_uses_sixty_distinct_interior_styles(self):
        values = {'environment': '室内'}
        seen = []
        for _ in range(60):
            values = self.engine.draw(values, ['environment'])
            seen.append(values['architecture'])
        self.assertEqual(set(seen), set(INTERIOR_STYLES))
        self.assertEqual(len(set(seen)), 60)
        self.assertNotIn('architecture', self.engine.bags)
        prompt = make_prompt(values)
        self.assertIn('内部装潢风格：', prompt)
        self.assertNotIn('门店建筑风格：', prompt)

    def test_switch_overrides_incompatible_style_lock(self):
        old = self.engine.draw({'environment': '室外'}, ['environment'])
        new = self.engine.draw(old, ['architecture'])
        self.assertEqual(new['environment'], '室内')
        self.assertIn(new['architecture'], INTERIOR_STYLES)
        locked = self.engine.draw(new, ['architecture', 'environment'])
        self.assertEqual(locked['architecture'], new['architecture'])

    def test_indoor_decor_pools_exhaust_independently(self):
        values = {'environment': '室内'}
        places, balloons = [], []
        for _ in range(24):
            values = self.engine.draw(values, ['environment'])
            places.append(values['placement'])
            balloons.append(values['balloons'])
        self.assertEqual(set(places), set(self.engine.pools['indoor_placement']))
        self.assertEqual(set(balloons), set(self.engine.pools['indoor_balloons']))
        self.assertNotIn('placement', self.engine.bags)
        self.assertNotIn('balloons', self.engine.bags)

    def test_scene_switch_replaces_locked_decor(self):
        outside = self.engine.draw({'environment': '室外'}, ['environment'])
        inside = self.engine.draw(outside, ['placement', 'balloons'])
        self.assertIn(inside['placement'], self.engine.pools['indoor_placement'])
        self.assertIn(inside['balloons'], self.engine.pools['indoor_balloons'])
        kept = self.engine.draw(inside, ['environment', 'placement', 'balloons'])
        self.assertEqual(kept['placement'], inside['placement'])
        self.assertEqual(kept['balloons'], inside['balloons'])

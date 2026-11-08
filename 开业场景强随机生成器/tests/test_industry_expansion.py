"""Expanded real candidates are scoped, reachable and remain overrideable."""
import random
import unittest
from scene_tool.domain.industry_profiles import profile, industry_pools
from scene_tool.config.paths import RESOURCES
from scene_tool.config.render_styles import BUYER,COMMERCIAL
from scene_tool.generation.parameters import Randomizer
from scene_tool.storage.pools import load_pools

class ExpansionTests(unittest.TestCase):
    def test_counts_and_brand_cycle_in_every_industry(self):
        for name in ('美业','服装','咖啡','餐饮','花店','家居','通用'):
            data=profile(name)
            self.assertEqual(len(set(data['brands'])),24)
            for key in ('logos','interiors','exteriors','inside_positions','outside_positions'):
                self.assertEqual(len(set(data[key])),12,(name,key))
            e=Randomizer(load_pools(RESOURCES/'pools.json'),random.Random(12))
            v={}
            seen=set()
            for _ in range(24):
                v=e.draw(v,render_style=BUYER,industry=name)
                # Keep the context stable so a complete bag is tested.
                v['environment']='室内'
            e.bags={}
            for _ in range(24):
                v=e.draw(v,['environment'],render_style=COMMERCIAL,industry=name)
                seen.add(v['brand'])
            self.assertEqual(seen,set(data['brands']))

    def test_custom_pool_is_not_replaced_by_expanded_default(self):
        e=Randomizer(load_pools(RESOURCES/'pools.json'),random.Random(1))
        e.industry_overrides={'美业|室内|'+BUYER:{'brand':['我的甲','我的乙']}}
        v={'environment':'室内'}
        for _ in range(8):
            v=e.draw(v,['environment'],render_style=BUYER,industry='美业')
            self.assertIn(v['brand'],['我的甲','我的乙'])

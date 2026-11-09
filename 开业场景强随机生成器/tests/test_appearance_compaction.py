import unittest
from scene_tool.config.closeup import CLOSEUP
from scene_tool.domain.prompts import make_prompt
from scene_tool.domain.variants.generation import features
from test_variant_binding import opening_view


class AppearanceCompactionTests(unittest.TestCase):
    def test_default_preservation_is_fixed_and_not_a_fake_variant(self):
        view=opening_view(CLOSEUP)
        values=view.current()
        before=make_prompt(values,render_style=CLOSEUP)
        original=features(values,CLOSEUP,set())
        values.update(detail_surface='保持已有细节清楚',detail_art='保持局部真实形状')
        self.assertEqual(features(values,CLOSEUP,set()),original)
        self.assertEqual(make_prompt(values,render_style=CLOSEUP),before)
        for _ in range(5):
            new=view.engine.draw(values,render_style=CLOSEUP)
            self.assertEqual(new['detail_surface'],values['detail_surface'])
            self.assertEqual(new['detail_art'],values['detail_art'])

    def test_custom_appearance_pool_and_hide_remain_functional(self):
        view=opening_view(CLOSEUP)
        context='美业|'+(view.values['environment'].get() or '室外')+'|'+CLOSEUP
        view.engine.industry_overrides[context]={'detail_art':['自填补充甲','自填补充乙']}
        values=view.current()
        seen=set()
        for _ in range(4):
            values=view.engine.draw(values,render_style=CLOSEUP,industry='美业')
            seen.add(values['detail_art'])
            self.assertIn(values['detail_art'],make_prompt(values,render_style=CLOSEUP))
            self.assertNotIn(values['detail_art'],make_prompt(values,render_style=CLOSEUP,hidden={'detail_art'}))
        self.assertEqual(seen,{'自填补充甲','自填补充乙'})

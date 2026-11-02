import unittest
from scene_tool.config.closeup import CLOSEUP
from scene_tool.config.close_dimensions import DIMENSIONS
from scene_tool.domain.industry_profiles import dimensions
from scene_tool.domain.prompts import make_prompt
from scene_tool.domain.scene_model import SceneModel
from scene_tool.storage.scenes import load_profiles
from scene_tool.config.paths import RESOURCES
from scene_tool.storage.pools import load_pools
from scene_tool.generation.parameters import Randomizer


class CloseSchemaTests(unittest.TestCase):
    def test_opening_renders_only_active_fields(self):
        values = Randomizer(load_pools(RESOURCES/'pools.json')).draw({'brand':'旧品牌'}, render_style=CLOSEUP, industry='咖啡')
        prompt = make_prompt(values, copy='旧开业文案', render_style=CLOSEUP)
        for key, label in DIMENSIONS:
            self.assertIn(label + '：' + values[key], prompt)
        for text in ('旧开业文案', '旧品牌', '街道地址：', '门店建筑风格：'):
            self.assertNotIn(text, prompt)
        self.assertIn('brand', dict(dimensions('真实买家秀')))
        self.assertNotIn('brand', dict(dimensions(CLOSEUP)))

    def test_all_other_scenes_use_closeup_pools(self):
        for profile in load_profiles():
            model = SceneModel(profile, {'render_style':CLOSEUP})
            for _ in range(3):
                model.draw()
                prompt = model.generate()
                for label in ('细节主体','邻接边缘','原稿保留重点','近景机位','细节受光'):
                    self.assertIn(label + '：', prompt)
            model.render_style = '真实买家秀'
            self.assertEqual(model.active_profile(), profile)

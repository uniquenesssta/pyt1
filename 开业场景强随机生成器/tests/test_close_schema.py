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
                for label in ('细节主体','邻接边缘','外观保留重点','近景机位','亮光位置'):
                    self.assertIn(label + '：', prompt)
            model.render_style = '真实买家秀'
            self.assertEqual(model.active_profile(), profile)

    def test_free_subject_survives_draw_save_and_prompt(self):
        engine = Randomizer(load_pools(RESOURCES/'pools.json'))
        for subject in ('白瓷咖啡杯', '自行车后拨', ''):
            values = engine.draw({'close_subject': subject}, render_style=CLOSEUP, industry='美业')
            prompt = make_prompt(values, render_style=CLOSEUP)
            self.assertIn(subject or '参考图中的主体', prompt)
            for word in ('KT板', '气球', '美业', '开业现场', '3.5米'):
                self.assertNotIn(word, prompt)
            for profile in load_profiles():
                model = SceneModel(profile, {'close_subject':subject, 'render_style':CLOSEUP})
                model.draw()
                restored = SceneModel(profile, model.state())
                self.assertIn(subject or '参考图中的主体', restored.generate())

    def test_custom_material_persists_and_empty_does_not_guess(self):
        values = Randomizer(load_pools(RESOURCES/'pools.json')).draw({'close_material':'哑光红纸，局部烫金'}, render_style=CLOSEUP)
        self.assertIn('指定材质：哑光红纸，局部烫金', make_prompt(values, render_style=CLOSEUP))
        for profile in load_profiles():
            model = SceneModel(profile, {'render_style':CLOSEUP, 'close_material':values['close_material']})
            model.draw()
            restored = SceneModel(profile, model.state())
            self.assertIn('指定材质：哑光红纸，局部烫金', restored.generate())
            restored.close_material = ' '
            self.assertNotIn('指定材质：', restored.generate())

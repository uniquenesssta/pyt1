"""Real generation, schema, persistence and editing paths for industry modes."""
import random
import unittest
from copy import deepcopy
from scene_tool.config.paths import RESOURCES
from scene_tool.config.render_styles import BUYER, COMMERCIAL, normalize_style
from scene_tool.domain.industry_profiles import dimensions, industry_pools, profile, industry_key
from scene_tool.domain.prompts import make_prompt
from scene_tool.domain.scene_model import SceneModel
from scene_tool.domain.prompt_migration import migrate_prompt_state
from scene_tool.generation.parameters import Randomizer
from scene_tool.generation.copywriting import CopyRandomizer
from scene_tool.storage.pools import load_pools
from scene_tool.storage.scenes import load_profiles
from scene_tool.storage.scene_codec import encode_scene, decode_scene


class IndustryModesTests(unittest.TestCase):
    def engine(self):
        return Randomizer(load_pools(RESOURCES / 'pools.json'), random.Random(7))

    def test_old_style_name_migrates(self):
        self.assertEqual(normalize_style('商业主图'), COMMERCIAL)
        self.assertEqual(COMMERCIAL, '商业效果图')

    def test_commercial_has_real_new_keys_and_no_addresses(self):
        engine = self.engine()
        values = engine.draw({'environment': '室内', 'city': '旧城市', 'address': '旧街道'}, ['environment'], render_style=COMMERCIAL, industry='美业')
        prompt = make_prompt(values, industry='美业', render_style=COMMERCIAL)
        self.assertIn('商业展示空间：', prompt)
        self.assertIn('背景层次：', prompt)
        for forbidden in ('旧城市', '旧街道', '街道地址', '本轮参数中的原文；开业文案和地址'):
            self.assertNotIn(forbidden, prompt)
        self.assertNotIn('city', dict(dimensions(COMMERCIAL)))
        self.assertNotIn('address', dict(dimensions(COMMERCIAL)))
        self.assertEqual(len(dimensions(COMMERCIAL)), 12)

    def test_every_industry_and_environment_only_draws_its_pool(self):
        for industry in ('美业', '服装', '咖啡', '餐饮', '花店', '家居', '通用'):
            for style in (BUYER, COMMERCIAL):
                for environment in ('室内', '室外'):
                    engine = self.engine()
                    current = {'environment': environment}
                    scoped = industry_pools(industry, environment, style)
                    for _ in range(30):
                        before = dict(current)
                        current = engine.draw(current, ['environment'], render_style=style, industry=industry)
                        for key, pool in scoped.items():
                            self.assertIn(current[key], pool)
                            if key in before: self.assertNotEqual(before[key], current[key])
                    text = make_prompt(current, industry=industry, render_style=style)
                    self.assertIn('本轮行业：' + industry, text)

    def test_industry_content_is_not_shared_beauty_pool(self):
        beauty = industry_pools('美业', '室内', BUYER)
        for industry in ('服装', '咖啡', '餐饮', '花店', '通用'):
            other = industry_pools(industry, '室内', BUYER)
            for key in ('architecture', 'placement', 'brand', 'logo_shape', 'logo_structure'):
                self.assertFalse(set(beauty[key]) & set(other[key]), (industry, key))

    def test_industry_copy_uses_own_sublines(self):
        engine = CopyRandomizer(random.Random(4))
        for industry in ('美业', '服装', '咖啡', '餐饮', '花店', '通用'):
            current = ''
            for _ in range(250):
                current = engine.draw(current, industry=industry)
                self.assertTrue(any(x in current for x in profile(industry_key(industry))['copy']))

    def test_custom_context_pool_used_and_saved_bag_resumes(self):
        engine = self.engine()
        engine.industry_overrides = {'咖啡|室内|' + COMMERCIAL: {'brand': ['我的咖啡甲', '我的咖啡乙', '我的咖啡丙']}}
        current = engine.draw({'environment': '室内'}, ['environment'], render_style=COMMERCIAL, industry='咖啡')
        self.assertIn(current['brand'], engine.industry_overrides['咖啡|室内|' + COMMERCIAL]['brand'])
        restored = self.engine()
        restored.industry_overrides = deepcopy(engine.industry_overrides)
        restored.restore_bags(engine.bags)
        self.assertEqual(restored.bags, engine.bags)
        following = restored.draw(current, ['environment', 'brand'], render_style=COMMERCIAL, industry='咖啡')
        self.assertEqual(following['brand'], current['brand'])
        other = restored.scoped_pools('美业', '室内', COMMERCIAL)
        self.assertNotIn('我的咖啡甲', other['brand'])

    def test_seven_scenes_switch_layout_and_persist_commercial_pools(self):
        for original in load_profiles():
            model = SceneModel(original)
            model.render_style = COMMERCIAL
            model.draw()
            model.regenerate()
            self.assertEqual(model.active_profile()['dimensions'][5]['label'], '主体展示构图')
            self.assertIn('默认无人', model.values[original['dimensions'][5]['key']])
            self.assertIn('商业装置布局：', model.prompt)
            key = original['dimensions'][2]['key']
            model.commercial_pools[key] = ['自选布局甲', '自选布局乙']
            loaded = SceneModel(original, decode_scene(original, encode_scene(model)))
            loaded.draw()
            self.assertIn(loaded.values[key], model.commercial_pools[key])
            loaded.render_style = BUYER
            self.assertEqual(loaded.active_profile(), original)

    def test_old_commercial_session_gets_new_schema_without_losing_manual_prompt(self):
        values = self.engine().draw()
        state = dict(values=values, render_style='商业主图', prompt='old', rendered='old')
        migrated = migrate_prompt_state(state, ())
        self.assertIn('商业展示空间', migrated['prompt'])
        state['prompt'] = '手改整段'
        self.assertEqual(migrate_prompt_state(state, ())['prompt'], '手改整段')

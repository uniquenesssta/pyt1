"""Regression checks for candidate coverage, prompt boundaries and old settings."""
import json
import random
import unittest
from copy import deepcopy
from types import SimpleNamespace

from scene_tool.config.closeup import CLOSEUP
from scene_tool.config.defaults import DEFAULT_CONSTRAINTS
from scene_tool.config.paths import RESOURCES
from scene_tool.config.prompt_contract import RESOLVED_PARAMETERS
from scene_tool.config.render_styles import BUYER, COMMERCIAL, RENDER_STYLES
from scene_tool.config.studio_shots import SHOTS, camera_family
from scene_tool.domain.commercial_migration import placement_updates
from scene_tool.domain.commercial_scenes import scene_profile
from scene_tool.domain.prompts import make_prompt
from scene_tool.domain.prompt_migration import migrate_prompt_state
from scene_tool.domain.scene_model import SceneModel
from scene_tool.generation.industry import draw_industry
from scene_tool.generation.parameters import Randomizer
from scene_tool.storage.pools import load_pools
from scene_tool.storage.scenes import load_profiles


class PromptAuditTests(unittest.TestCase):
    def engine(self):
        return Randomizer(load_pools(RESOURCES / 'pools.json'), random.Random(17))

    def test_commercial_full_placement_pool_is_reachable_without_frame_directives(self):
        for profile in load_profiles():
            original = profile['dimensions'][2]
            actual = scene_profile(profile, COMMERCIAL)['dimensions'][2]
            self.assertEqual(actual['options'], original['options'])
            model = SceneModel(profile, {'render_style': COMMERCIAL}, random.Random(18))
            seen = {model.values[original['key']]}
            for _ in range(len(actual['options']) - 1):
                model.draw()
                seen.add(model.values[original['key']])
            self.assertEqual(seen, set(original['options']))
            for value in actual['options']:
                for forbidden in ('主体居中', '主体偏左', '主体偏右'):
                    self.assertNotIn(forbidden, value)

    def test_prefer_changed_base_without_losing_exhaustion_or_lock(self):
        engine = SimpleNamespace(rng=random.Random(3), bags={})
        pool = ['甲；细节一', '甲；细节二', '乙；细节一', '乙；细节二']
        previous = ''
        seen = []
        for _ in pool:
            previous = draw_industry(engine, 'architecture', pool, previous, False, '美业', '室内', BUYER)
            seen.append(previous)
        self.assertEqual(set(seen), set(pool))
        self.assertTrue(all(a[0] != b[0] for a,b in zip(seen, seen[1:])))
        before = deepcopy(engine.bags)
        self.assertEqual(draw_industry(engine, 'architecture', pool, previous, True, '美业', '室内', BUYER), previous)
        self.assertEqual(engine.bags, before)

    def test_legacy_placement_locks_and_custom_overrides_migrate(self):
        for profile in load_profiles():
            key = profile['dimensions'][2]['key']
            mapping = placement_updates(profile)
            old = next(iter(mapping))
            state = {'render_style': COMMERCIAL, 'values': {key:old}, 'locks':{key:True},
                     'commercial_pools':{key:list(mapping)}}
            saved = deepcopy(state)
            model = SceneModel(profile, state)
            self.assertEqual(state, saved)
            self.assertEqual(model.values[key], mapping[old])
            model.draw()
            self.assertEqual(model.values[key], mapping[old])
            self.assertEqual(len(model.active_pools()[key]), 40)
            state['commercial_pools'][key] = [old, '手写：主体偏右，保留我的选择']
            model = SceneModel(profile, state)
            self.assertIn('手写：主体偏右，保留我的选择', model.active_pools()[key])

    def test_generated_scene_prompts_refresh_but_manual_edits_survive(self):
        for profile in load_profiles():
            model = SceneModel(profile)
            state = model.state()
            state.update(prompt='旧生成文', rendered='旧生成文')
            self.assertNotEqual(SceneModel(profile, state).prompt, '旧生成文')
            state['prompt'] = '用户逐字编辑，不许替换'
            self.assertEqual(SceneModel(profile, state).prompt, state['prompt'])

    def test_legacy_opening_defaults_upgrade_and_custom_text_is_untouched(self):
        old = json.loads((RESOURCES / 'legacy_prompt_v3.json').read_text())['constraints']
        v = self.engine().draw()
        state = dict(values=v, constraints=old, prompt='旧', rendered='旧', locks={'camera':True})
        new = migrate_prompt_state(state, (old,))
        self.assertEqual(new['constraints'], DEFAULT_CONSTRAINTS)
        self.assertEqual(new['locks'], state['locks'])
        self.assertNotIn('尺寸与空间：', new['prompt'])
        state.update(constraints=old+'\n我自己的要求', prompt='手改内容')
        self.assertEqual(migrate_prompt_state(state, (old,)), state)

    def test_three_modes_preserve_all_visible_fields_and_one_contract(self):
        for style in RENDER_STYLES:
            v=self.engine().draw({'close_subject':'对联','close_material':'写真布背胶'},
                                 render_style=style, industry='美业')
            text=make_prompt(v,render_style=style,extra='我的补充原文')
            self.assertEqual(text.count(RESOLVED_PARAMETERS),1)
            self.assertTrue(text.endswith('我的补充原文'))
            if style==CLOSEUP:
                self.assertNotIn('街道地址',text)
                self.assertNotIn('3.5米',text)
                self.assertIn('单幅绝不复制',text)
            elif style==COMMERCIAL:
                self.assertNotIn('街道地址',text)
                self.assertNotIn('生活化细节',text)
                self.assertIn('75—150mm',text)
            else:
                self.assertIn('未经精修',text)

    def test_closeup_family_cycle_and_locks_still_work_in_eight_scenes(self):
        engine=self.engine()
        values={}
        names=[]
        for _ in range(6):
            values=engine.draw(values,render_style=CLOSEUP)
            names.append(camera_family(values['camera']))
        self.assertEqual(set(names[:3]),set(SHOTS))
        self.assertEqual(set(names[3:]),set(SHOTS))
        for profile in load_profiles():
            m=SceneModel(profile,{'render_style':CLOSEUP},random.Random(4))
            m.locks['camera']=True
            camera=m.values['camera']
            for _ in range(8):
                m.draw()
                self.assertEqual(m.values['camera'],camera)
                self.assertIn(camera,m.generate())
            m.hidden['camera']=True
            self.assertNotIn(camera,m.generate())

    def test_custom_requirements_not_shortened_and_hidden_fields_omitted(self):
        custom='自填约束；保留这一长段；不要按分号截断'
        for style in RENDER_STYLES:
            values=self.engine().draw(render_style=style)
            values['ratio']='13:7独特比例'
            text=make_prompt(values,constraints=custom,hidden={'ratio','camera'},render_style=style)
            self.assertIn(custom,text)
            self.assertNotIn(values['ratio'],text)
            self.assertNotIn(values['camera'],text)

    def test_old_layer_preset_lock_is_upgraded_without_adding_layers(self):
        v=self.engine().draw({'detail_layers':'相邻部件形成前后层次'},
                             ['detail_layers'],render_style=CLOSEUP)
        self.assertIn('不增加叠层', v['detail_layers'])
        v['detail_layers']='自定义叠层展示'
        self.assertEqual(self.engine().draw(v,['detail_layers'],render_style=CLOSEUP)['detail_layers'],v['detail_layers'])

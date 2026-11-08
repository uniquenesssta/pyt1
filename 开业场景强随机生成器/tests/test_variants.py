"""Exercise real alternative selection, isolated state and prompt application."""
import copy
import random
import unittest

from scene_tool.config.closeup import CLOSEUP
from scene_tool.config.defaults import DEFAULT_CONSTRAINTS
from scene_tool.config.paths import RESOURCES
from scene_tool.config.product_size import FOLLOW_REFERENCE
from scene_tool.config.render_styles import RENDER_STYLES
from scene_tool.config.studio_shots import SHOTS
from scene_tool.domain.industry_profiles import dimensions
from scene_tool.domain.prompts import make_prompt
from scene_tool.domain.scene_model import SceneModel
from scene_tool.domain.variants.generation import opening_variants,scene_variants
from scene_tool.generation.parameters import Randomizer
from scene_tool.storage.pools import load_pools
from scene_tool.storage.scenes import load_profiles
from scene_tool.storage.scene_codec import encode_scene,decode_scene

class VariantTests(unittest.TestCase):
    def setUp(self):
        self.engine=Randomizer(load_pools(RESOURCES/'pools.json'),random.Random(47))

    def options(self,style,values,locks=(),hidden=()):
        return opening_variants(self.engine,values,locks,style=style,industry='美业',
                 constraints=DEFAULT_CONSTRAINTS,copyline='同一套文案',hidden=hidden)

    def test_opening_preview_does_not_consume_live_state_and_keeps_content(self):
        for style in RENDER_STYLES:
            v=self.engine.draw({'close_subject':'对联','close_material':'我的材质'},render_style=style,industry='美业')
            before=(copy.deepcopy(v),copy.deepcopy(self.engine.bags),self.engine.rng.getstate(),copy.deepcopy(self.engine.recent))
            plans=self.options(style,v)
            self.assertEqual(len(plans),4)
            self.assertEqual(len({p.prompt for p in plans}),4)
            self.assertEqual(before,(v,self.engine.bags,self.engine.rng.getstate(),self.engine.recent))
            for plan in plans:
                values=plan.payload['values']
                for key in ('brand','logo_shape','logo_structure','ratio','close_subject','close_material'):
                    self.assertEqual(values.get(key),v.get(key))
                rebuilt=make_prompt(values,industry='美业',constraints=DEFAULT_CONSTRAINTS,copy='同一套文案',render_style=style,product_size=FOLLOW_REFERENCE)
                self.assertEqual(plan.prompt,rebuilt)
            if style==CLOSEUP:
                self.assertEqual({p.features['镜头类别'] for p in plans[:3]},set(SHOTS))

    def test_locks_are_honoured_and_insufficient_options_are_not_duplicated(self):
        values=self.engine.draw(render_style=CLOSEUP)
        keys=[k for k,_ in dimensions(CLOSEUP)]
        one=self.options(CLOSEUP,values,keys)
        self.assertEqual(len(one),1)
        plans=self.options(CLOSEUP,values,['camera','detail_light','detail_reflection'])
        for plan in plans:
            for key in ('camera','detail_light','detail_reflection'):
                self.assertEqual(plan.payload['values'][key],values[key])

    def test_hidden_changes_do_not_create_fake_distinct_variants(self):
        values=self.engine.draw(render_style=CLOSEUP)
        all_keys={k for k,_ in dimensions(CLOSEUP)}
        self.assertEqual(len(self.options(CLOSEUP,values,hidden=all_keys)),1)

    def test_empty_design_fields_are_filled_once_for_the_whole_batch(self):
        values=self.engine.draw(render_style='商业效果图',industry='美业')
        keys=('brand','logo_shape','logo_structure','ratio')
        for key in keys: values[key]=''
        plans=self.options('商业效果图',values)
        self.assertEqual(len(plans),4)
        for key in keys:
            chosen={p.payload['values'][key] for p in plans}
            self.assertEqual(len(chosen),1)
            self.assertNotIn('',chosen)

    def test_seven_scenes_and_three_modes_apply_and_persist_exact_prompt(self):
        for profile in load_profiles():
            for style in RENDER_STYLES:
                model=SceneModel(profile,dict(render_style=style,close_subject='我的产品',close_material='我的材质'),random.Random(11))
                model.locks['ratio']=True
                before=copy.deepcopy(model.state())
                rng=model.rng.getstate()
                plans=scene_variants(model)
                self.assertEqual(len(plans),4)
                self.assertEqual(model.state(),before)
                self.assertEqual(model.rng.getstate(),rng)
                selected=plans[2]
                model.values=dict(selected.payload['values'])
                model.bags=copy.deepcopy(selected.payload['bags'])
                model.regenerate()
                self.assertEqual(model.prompt,selected.prompt)
                restored=SceneModel(profile,decode_scene(profile,encode_scene(model)))
                self.assertEqual(restored.generate(),selected.prompt)
                self.assertEqual(restored.close_subject,'我的产品')
                self.assertEqual(restored.close_material,'我的材质')

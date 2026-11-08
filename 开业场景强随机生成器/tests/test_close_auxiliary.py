"""Merged output must retain individual user choices and visibility controls."""
import unittest
from scene_tool.config.closeup import CLOSEUP
from scene_tool.config.close_auxiliary import KEYS
from scene_tool.config.paths import RESOURCES
from scene_tool.domain.prompts import make_prompt
from scene_tool.domain.scene_model import SceneModel
from scene_tool.generation.parameters import Randomizer
from scene_tool.storage.pools import load_pools
from scene_tool.storage.scenes import load_profiles
from scene_tool.storage.scene_codec import encode_scene,decode_scene

class CloseAuxiliaryTests(unittest.TestCase):
    def test_opening_keeps_custom_text_locks_and_individual_hide(self):
        engine=Randomizer(load_pools(RESOURCES/'pools.json'))
        values={k:'手写_'+k for k in KEYS}
        values=engine.draw(values,KEYS,render_style=CLOSEUP)
        text=make_prompt(values,render_style=CLOSEUP)
        for key in KEYS:
            self.assertIn(values[key],text)
            hidden=make_prompt(values,render_style=CLOSEUP,hidden={key})
            self.assertNotIn(values[key],hidden)
        lines=text.splitlines()
        self.assertEqual(sum('手写_' in line for line in lines),2)

    def test_scene_auxiliary_values_roundtrip_under_original_storage_keys(self):
        for profile in load_profiles():
            model=SceneModel(profile,dict(render_style=CLOSEUP))
            keys={d['key'] for d in model.active_profile()['dimensions'] if d.get('close_key') in KEYS}
            for k in keys:
                model.values[k]='我的辅助_'+k
                model.locks[k]=True
            model.draw()
            model.regenerate()
            restored=SceneModel(profile,decode_scene(profile,encode_scene(model)))
            for k in keys:
                self.assertEqual(restored.values[k],model.values[k])
                self.assertTrue(restored.locks[k])
                self.assertIn(model.values[k],restored.prompt)
                restored.hidden[k]=True
                self.assertNotIn(model.values[k],restored.generate())

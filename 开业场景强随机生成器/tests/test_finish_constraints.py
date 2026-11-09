import copy
import json
import random
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from scene_tool.config.closeup import CLOSEUP
from scene_tool.config.material_finish import OPTIONS, FOLLOW, MATTE, SOFT, GLOSS, effective
from scene_tool.config.random_strategy import PRIMARY, ALL
from scene_tool.domain.material_finish import compatible
from scene_tool.domain.prompts import make_prompt
from scene_tool.domain.scene_model import SceneModel
from scene_tool.domain.variants.generation import opening_variants, scene_variants
from scene_tool.generation.strategy import draw_opening, draw_scene
from scene_tool.storage import material_presets
from scene_tool.storage.scenes import load_profiles
from scene_tool.storage.scene_codec import encode_scene,decode_scene
from scene_tool.ui.material_binding import apply_material
from test_variant_binding import opening_view,Value


class FinishConstraintTests(unittest.TestCase):
    def test_opening_both_strategies_and_four_variants_follow_finish(self):
        for finish in OPTIONS:
            for strategy in (PRIMARY,ALL):
                view=opening_view(CLOSEUP)
                values=view.current()
                values['close_finish']=finish
                values=view.engine.draw(values,render_style=CLOSEUP)
                for step in range(16):
                    values,_=draw_opening(view.engine,values,(),strategy=strategy,hidden=(),
                        strong=True,style=CLOSEUP,industry='美业',step=step)
                    self.assertTrue(compatible(finish,values['detail_reflection'],values['detail_light']))
                    if finish==MATTE: self.assertEqual(values['detail_light'],'无明显光带')
                    self.assertTrue(make_prompt(values,render_style=CLOSEUP))
                plans=opening_variants(view.engine,values,(),style=CLOSEUP,industry='美业',
                    constraints=view.constraints.get(),copyline='')
                self.assertEqual(len(plans),4)
                for p in plans:
                    v=p.payload['values']
                    self.assertEqual(v['close_finish'],finish)
                    self.assertTrue(compatible(finish,v['detail_reflection'],v['detail_light']))

    def test_all_scenes_draw_restore_and_preview_respect_finish(self):
        for profile in load_profiles():
            for finish in (MATTE,SOFT,GLOSS):
                model=SceneModel(profile,{'render_style':CLOSEUP,'close_finish':finish},random.Random(8))
                key=next(d['key'] for d in model.active_profile()['dimensions'] if d.get('close_key')=='detail_light')
                for strategy in (PRIMARY,ALL):
                    model.random_strategy=strategy
                    for step in range(6):
                        draw_scene(model,step)
                        self.assertTrue(compatible(finish,model.values['detail_reflection'],model.values[key]))
                model.regenerate()
                restored=SceneModel(profile,decode_scene(profile,encode_scene(model)))
                self.assertEqual(restored.close_finish,finish)
                self.assertEqual(restored.prompt,model.prompt)
                for p in scene_variants(model):
                    self.assertTrue(compatible(finish,p.payload['values']['detail_reflection'],p.payload['values'][key]))

    def test_direct_prompt_rejects_conflict_and_resolves_follow_material(self):
        view=opening_view(CLOSEUP)
        values=view.current()
        values.update(close_finish=MATTE,detail_reflection='高光',detail_light='中间亮，两侧不亮')
        with self.assertRaises(ValueError): make_prompt(values,render_style=CLOSEUP)
        values.update(detail_reflection='跟随材质',detail_light='无明显光带')
        text=make_prompt(values,render_style=CLOSEUP)
        self.assertIn('表面反光：哑光',text)
        self.assertNotIn('中间亮，两侧不亮',text)
        values['detail_light']='手写未知亮带'
        with self.assertRaises(ValueError): view.engine.draw(values,['detail_light'],render_style=CLOSEUP)

    def test_conflicting_lock_does_not_consume_bags_or_change_ui(self):
        view=opening_view(CLOSEUP)
        view.values['detail_reflection'].set('高光')
        view.values['detail_light'].set('中间亮，两侧不亮')
        view.locks['detail_reflection'].set(True)
        view.set_prompt(view.generated())
        before=(view.current(),copy.deepcopy(view.engine.bags),view.prompt.get())
        with patch('scene_tool.ui.material_binding.messagebox.showwarning') as warning:
            self.assertFalse(apply_material(view,'哑光纸',finish=MATTE))
            warning.assert_called_once()
        self.assertEqual(before,(view.current(),view.engine.bags,view.prompt.get()))
        source=dict(view.current(),close_finish=MATTE)
        with self.assertRaises(ValueError): view.engine.draw(source,['detail_reflection'],render_style=CLOSEUP)
        self.assertEqual(view.engine.bags,before[1])

    def test_apply_finish_changes_only_incompatible_reflection_and_saves(self):
        view=opening_view(CLOSEUP)
        view.values['detail_reflection'].set('高光')
        view.values['detail_light'].set('中间亮，两侧不亮')
        view.set_prompt(view.generated())
        camera=view.values['camera'].get()
        with tempfile.TemporaryDirectory() as folder, patch('scene_tool.ui.session_binding.DATA',Path(folder)):
            self.assertTrue(apply_material(view,'哑光红纸',finish=MATTE))
            state=json.loads((Path(folder)/'state.json').read_text())
        self.assertEqual(view.values['camera'].get(),camera)
        self.assertEqual(view.values['detail_light'].get(),'无明显光带')
        self.assertEqual(effective(MATTE,view.values['detail_reflection'].get()),MATTE)
        self.assertEqual(state['values']['close_finish'],MATTE)
        self.assertEqual(view.generated(),state['prompt'])
        self.assertEqual(view.combos['detail_light'].configure.call_args.kwargs['values'],['无明显光带'])

    def test_scene_finish_application_and_manual_cancel_are_atomic(self):
        profile=load_profiles()[0]
        model=SceneModel(profile,{'render_style':CLOSEUP})
        panel=SimpleNamespace(model=model,close_material=Value(''),close_finish=Value(FOLLOW),
            values={k:Value(v) for k,v in model.values.items()},updating=False,
            allow_replace=Mock(return_value=True),show_prompt=Mock(),persist=Mock())
        def capture():
            model.values={k:v.get() for k,v in panel.values.items()}
            model.close_material=panel.close_material.get()
            model.close_finish=panel.close_finish.get()
        panel.capture=capture
        self.assertTrue(apply_material(panel,'平滑红纸',True,finish=MATTE))
        self.assertIn('材质表面：哑光',model.prompt)
        before=copy.deepcopy(model.state())
        panel.allow_replace.return_value=False
        self.assertFalse(apply_material(panel,'新材质',True,finish=GLOSS))
        self.assertEqual(model.state(),before)

    def test_legacy_preset_migrates_without_guessing_finish_and_preserves_others(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'material_presets.json'
            path.write_text(json.dumps({'旧哑光':'写着哑光也不猜属性','旧亮面':'原文'}),encoding='utf8')
            old=path.read_bytes()
            data=material_presets.load(path)
            self.assertEqual(data['旧哑光']['finish'],FOLLOW)
            self.assertEqual(path.read_bytes(),old)
            material_presets.save('新纸','完整材质描述',path,finish=MATTE)
            self.assertEqual(material_presets.load(path)['旧亮面']['description'],'原文')
            self.assertEqual(material_presets.load(path)['新纸']['finish'],MATTE)
            before=path.read_bytes()
            with self.assertRaises(ValueError): material_presets.save('错误','新描述',path,finish='未知属性')
            self.assertEqual(path.read_bytes(),before)


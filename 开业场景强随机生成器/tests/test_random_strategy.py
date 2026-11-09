import copy
import random
import unittest
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from scene_tool.config.random_strategy import PRIMARY, ALL, CLOSE_MAIN, CLOSE_GROUPS
from scene_tool.config.closeup import CLOSEUP
from scene_tool.config.render_styles import RENDER_STYLES
from scene_tool.config.studio_shots import camera_family, SHOTS
from scene_tool.config import highlight_position as light, surface_reflection as reflection
from scene_tool.domain.scene_model import SceneModel
from scene_tool.domain.variants.generation import clone_engine
from scene_tool.generation.strategy import draw_opening, draw_scene
from scene_tool.storage.scenes import load_profiles
from scene_tool.storage.scene_codec import encode_scene, decode_scene
from test_variant_binding import opening_view, Value


class RandomStrategyTests(unittest.TestCase):
    def opening(self, view, step, strategy=PRIMARY, locks=(),hidden=()):
        return draw_opening(view.engine,view.current(),locks,strategy=strategy,hidden=hidden,
            strong=True,style=view.render_style.get(),industry='美业',step=step)

    def test_primary_close_cycles_all_auxiliary_groups_and_keeps_coupling(self):
        view=opening_view(CLOSEUP)
        changed=set()
        families=set()
        rotating=[g for g in CLOSE_GROUPS if g!=('detail_surface','detail_art')]
        for step in range(15):
            old=view.current()
            values,_=self.opening(view,step)
            family=camera_family(values['camera'])
            families.add(family)
            for key in CLOSE_MAIN:
                self.assertIn(values[key],SHOTS[family][key])
            self.assertTrue(light.compatible(values[reflection.KEY],values[light.KEY]))
            expected=set(rotating[step%len(rotating)])
            for group in CLOSE_GROUPS:
                for key in group:
                    if values[key]!=old[key]:
                        self.assertIn(key,expected)
                        changed.add(key)
                    view.values[key].set(values[key])
            for key in CLOSE_MAIN: view.values[key].set(values[key])
        self.assertEqual(families,set(SHOTS))
        self.assertTrue(set(k for g in rotating for k in g)<=changed)

    def test_locked_custom_values_hidden_controls_and_context_are_preserved(self):
        view=opening_view('商业效果图')
        view.values['architecture'].set('手写室内空间')
        view.values['environment'].set('室内')
        old=view.current()
        for step in range(8):
            values,_=self.opening(view,step,locks=('architecture','brand'),hidden=('lighting',))
            for key in ('architecture','brand','environment','lighting'):
                self.assertEqual(values[key],old[key])

    def test_all_mode_is_the_original_draw_and_primary_copy_rotates(self):
        for style in RENDER_STYLES:
            view=opening_view(style)
            engine=clone_engine(view.engine)
            values,change_copy=self.opening(view,0,ALL)
            self.assertEqual(values,engine.draw(view.current(),(),True,style,'美业'))
            if style!=CLOSEUP:
                flags=[self.opening(view,n)[1] for n in range(4)]
                self.assertIn(True,flags)
                self.assertIn(False,flags)

    def test_seven_scenes_three_modes_keep_locks_and_resume_strategy(self):
        for profile in load_profiles():
            for style in RENDER_STYLES:
                model=SceneModel(profile,{'render_style':style},random.Random(37))
                model.locks['ratio']=True
                locked_ratio=model.values['ratio']
                saved_locks=copy.deepcopy(model.locks)
                for step in range(10):
                    draw_scene(model,step)
                    model.strategy_step=step+1
                    model.regenerate()
                    self.assertEqual(model.locks,saved_locks)
                    self.assertEqual(model.values['ratio'],locked_ratio)
                    self.assertTrue(model.prompt)
                restored=SceneModel(profile,decode_scene(profile,encode_scene(model)))
                self.assertEqual(restored.random_strategy,PRIMARY)
                self.assertEqual(restored.strategy_step,10)
                self.assertEqual(restored.prompt,model.prompt)
                restored.random_strategy=ALL
                restored.rng=random.Random(25)
                expected=clone_engine(restored)
                draw_scene(restored)
                expected.draw()
                self.assertEqual(restored.values,expected.values)

    def test_normal_button_uses_policy_and_keeps_temporary_holds_after_ui_sync(self):
        from scene_tool.ui.window import App
        view=opening_view(CLOSEUP)
        view.values['detail_art'].set('我的原稿保留说明')
        view.random_strategy=Value(PRIMARY)
        view.strategy_step=0
        view.refresh=Mock()
        view.save=Mock()
        view.prompt.set(view.generated())
        view.rendered=view.prompt.get()
        App.randomize(view)
        self.assertEqual(view.values['detail_art'].get(),'我的原稿保留说明')
        self.assertEqual(view.strategy_step,1)
        view.refresh.assert_called_once()
        view.save.assert_called_once()

    def test_auxiliary_fields_are_built_directly_on_main_panel(self):
        from scene_tool.ui.parameter_panel import build_parameters
        from scene_tool.config.close_dimensions import LABELS
        from scene_tool.config.close_auxiliary import KEYS
        view=opening_view(CLOSEUP)
        with patch('scene_tool.ui.parameter_panel.ResultList') as results, patch('scene_tool.ui.material_presets.material_preset_row'):
            build_parameters(view,Mock(winfo_children=lambda: []))
        labels={call.args[0] for call in results.return_value.result.call_args_list}
        self.assertTrue({LABELS[k] for k in KEYS}<=labels)
        self.assertTrue(set(KEYS)<=set(view.combos))

    def test_scene_mode_sync_does_not_hide_auxiliary_rows(self):
        from scene_tool.ui.camera_binding import sync_scene_camera
        from scene_tool.config.close_auxiliary import KEYS
        for profile in load_profiles():
            model=SceneModel(profile,{'render_style':CLOSEUP})
            panel=SimpleNamespace(model=model,group_labels=[],reflection_row_index=4,
                material_preset_row_index=3,material_row_index=2,material_finish_row_index=5,
                values={k:Value(v) for k,v in model.values.items()},
                combos={k:Mock() for k in model.values},parameter_labels={k:Mock() for k in model.values})
            for key in ('size_row','subject_row','reflection_row','material_row','material_preset_row','material_finish_row'):
                setattr(panel,key,Mock(grid_info=lambda:{'row':2}))
            sync_scene_camera(panel)
            for d in model.active_profile()['dimensions']:
                if d.get('close_key') in KEYS:
                    panel.parameter_labels[d['key']].master.grid_remove.assert_not_called()

    def test_opening_strategy_and_rotation_resume_from_saved_state(self):
        from scene_tool.ui.session_binding import restore
        view=opening_view(CLOSEUP)
        view.random_strategy=Value(ALL)
        view.strategy_step=9
        view.startup_errors=[]
        with tempfile.TemporaryDirectory() as folder, patch('scene_tool.ui.session_binding.DATA',Path(folder)):
            view.save()
            view.random_strategy.set(PRIMARY)
            view.strategy_step=0
            restore(view)
        self.assertEqual(view.random_strategy.get(),ALL)
        self.assertEqual(view.strategy_step,9)
        self.assertEqual(view.startup_errors,[])


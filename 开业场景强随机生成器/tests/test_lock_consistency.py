import copy
import random
import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from scene_tool.config.render_styles import RENDER_STYLES, COMMERCIAL, CLOSEUP
from scene_tool.config.random_strategy import PRIMARY, ALL
from scene_tool.domain.scene_model import SceneModel
from scene_tool.generation.strategy import draw_opening,draw_scene
from scene_tool.storage.scenes import load_profiles
from scene_tool.ui.window import App
from test_variant_binding import opening_view,Value


class LockConsistencyTests(unittest.TestCase):
    def test_opening_both_strategies_keep_custom_locks_through_ui_sync(self):
        for strategy in (PRIMARY,ALL):
            for style in RENDER_STYLES:
                view=opening_view(style)
                key='detail_art' if style==CLOSEUP else 'brand'
                view.values[key].set('手写锁定内容')
                view.locks[key].set(True)
                view.random_strategy=Value(strategy)
                view.strategy_step=0
                view.refresh=Mock()
                view.save=Mock()
                view.set_prompt(view.generated())
                for _ in range(6):
                    App.randomize(view)
                    self.assertEqual(view.values[key].get(),'手写锁定内容')
                    self.assertTrue(view.locks[key].get())

    def test_seven_scene_custom_locks_survive_both_strategies_and_restart(self):
        for profile in load_profiles():
            for style in RENDER_STYLES:
                for strategy in (PRIMARY,ALL):
                    model=SceneModel(profile,{'render_style':style,'random_strategy':strategy},random.Random(4))
                    key=profile['dimensions'][0]['key']
                    model.values[key]='手填场景条件'
                    model.locks[key]=True
                    for step in range(5): draw_scene(model,step)
                    self.assertEqual(model.values[key],'手填场景条件')
                    model.regenerate()
                    restored=SceneModel(profile,copy.deepcopy(model.state()))
                    self.assertEqual(restored.values[key],'手填场景条件')

    def test_locked_industry_field_does_not_consume_its_shuffle_bag(self):
        view=opening_view(COMMERCIAL)
        before={k:list(v) for k,v in view.engine.bags.items() if k.endswith('|brand')}
        for strategy in (PRIMARY,ALL):
            values,_=draw_opening(view.engine,view.current(),['brand'],strategy=strategy,
                hidden=(),strong=True,style=COMMERCIAL,industry='美业')
            self.assertEqual(values['brand'],view.values['brand'].get())
        after={k:list(v) for k,v in view.engine.bags.items() if k.endswith('|brand')}
        self.assertEqual(before,after)

    def test_commercial_camera_lock_does_not_unnecessarily_freeze_environment(self):
        for strategy in (PRIMARY,ALL):
            view=opening_view(COMMERCIAL)
            values=view.current()
            drawn,_=draw_opening(view.engine,values,['camera'],strategy=strategy,
                hidden=(),strong=True,style=COMMERCIAL,industry='美业')
            self.assertEqual(drawn['camera'],values['camera'])
            self.assertNotEqual(drawn['environment'],values['environment'])

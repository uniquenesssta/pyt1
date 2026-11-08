"""Exercise real UI callbacks and persistence without claiming native GUI coverage."""
import copy
import json
import random
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from scene_tool.config.closeup import CLOSEUP
from scene_tool.config.defaults import DEFAULT_CONSTRAINTS, DIMENSIONS
from scene_tool.config.paths import RESOURCES
from scene_tool.config.product_size import FOLLOW_REFERENCE
from scene_tool.config.render_styles import RENDER_STYLES
from scene_tool.domain.industry_profiles import EXTRA_DIMENSIONS
from scene_tool.domain.scene_model import SceneModel
from scene_tool.generation.copywriting import CopyRandomizer
from scene_tool.generation.parameters import Randomizer
from scene_tool.storage.pools import load_pools
from scene_tool.storage.scenes import load_profiles
from scene_tool.ui.prompt_controller import PromptController
from scene_tool.ui.session_binding import save as save_opening
from scene_tool.ui.variant_binding import open_opening_variants, open_scene_variants


class Value:
    def __init__(self, value): self.value = value
    def get(self, *_): return self.value
    def set(self, value): self.value = value
    def delete(self, *_): self.value = ''
    def insert(self, _, text): self.value = text


def opening_view(style):
    engine = Randomizer(load_pools(RESOURCES/'pools.json'), random.Random(5))
    values = {k:'' for k,_ in (*DIMENSIONS, *EXTRA_DIMENSIONS)}
    values.update(close_subject='我的产品', close_material='自填表面')
    values = engine.draw(values, render_style=style, industry='美业')
    values['brand'] = '用户自己写的品牌'
    view = SimpleNamespace(engine=engine, values={k:Value(v) for k,v in values.items()},
        locks={k:Value(False) for k in values}, hidden={k:Value(False) for k in values},
        render_style=Value(style), industry=Value('美业'), product_size=Value(FOLLOW_REFERENCE),
        constraints=Value(DEFAULT_CONSTRAINTS), extra=Value('保留我的补充要求'), copyline=Value('我的文案'),
        strong=Value(True), generated_names=Value(False), parameter_style=style,
        industry_context=('美业',values['environment'],style),
        combos={k:Mock() for k in values}, parameter_labels={k:Mock() for k in values},
        copy_random=Value(True),copy_locked=Value(False),copy_engine=CopyRandomizer(),
        prompt=Value(''),rendered='',status=Value(''),pending='scheduled',after_cancel=Mock(),
        ready=True,prompt_reset=SimpleNamespace(snapshot=('old',)),undo_reset_button=Mock())
    view.current = lambda: {k:v.get() for k,v in view.values.items()}
    controller = PromptController(view)
    view.generated, view.edited, view.set_prompt = controller.generated, controller.edited, controller.set_prompt
    view.save = lambda: save_opening(view)
    view.set_prompt(view.generated())
    return view


class VariantBindingTests(unittest.TestCase):
    def test_opening_preview_apply_saves_exact_visible_choice(self):
        for style in RENDER_STYLES:
            view = opening_view(style)
            before = (view.current(),copy.deepcopy(view.engine.bags),view.engine.rng.getstate())
            with patch('scene_tool.ui.variant_binding.show_variants') as show:
                open_opening_variants(view)
            self.assertEqual(before,(view.current(),view.engine.bags,view.engine.rng.getstate()))
            choices, apply = show.call_args.args[1:]
            choice = next((x for x in choices if x.payload['values']['environment'] != view.values['environment'].get()), choices[-1])
            with tempfile.TemporaryDirectory() as folder, patch('scene_tool.ui.session_binding.DATA',Path(folder)):
                self.assertTrue(apply(choice))
                saved=json.loads((Path(folder)/'state.json').read_text(encoding='utf-8-sig'))
            self.assertEqual(view.values['brand'].get(),'用户自己写的品牌')
            self.assertEqual(view.prompt.get(),choice.prompt)
            self.assertEqual(view.generated(),choice.prompt)
            self.assertEqual(saved['prompt'],choice.prompt)
            self.assertEqual(saved['rendered'],choice.prompt)
            self.assertEqual(saved['values'],view.current())
            self.assertFalse(view.engine.generated)
            self.assertIsNone(view.pending)

    def test_declining_to_replace_manual_prompt_leaves_current_state(self):
        view = opening_view(CLOSEUP)
        view.prompt.set('用户手改整段内容')
        before=(view.current(),view.engine,view.prompt.get(),view.pending)
        with patch('scene_tool.ui.variant_binding.show_variants') as show:
            open_opening_variants(view)
        choices,apply=show.call_args.args[1:]
        with patch('scene_tool.ui.variant_binding.messagebox.askyesno',return_value=False):
            self.assertFalse(apply(choices[0]))
        self.assertEqual(before,(view.current(),view.engine,view.prompt.get(),view.pending))

    def test_scene_apply_keeps_locked_custom_values_and_persists_visible_prompt(self):
        for profile in load_profiles():
            for style in RENDER_STYLES:
                model=SceneModel(profile,{'render_style':style},random.Random(17))
                key=profile['dimensions'][0]['key']
                model.values[key]='我的自填说明'
                model.locks[key]=True
                panel=SimpleNamespace(model=model,pause=Mock(),allow_replace=Mock(return_value=True),
                    values={k:Value(v) for k,v in model.values.items()},
                    combos={k:Mock() for k in model.values},updating=False)
                displayed=[]
                persisted=[]
                panel.show_prompt=lambda: displayed.append(model.prompt)
                panel.persist=lambda: persisted.append(copy.deepcopy(model.state()))
                before=copy.deepcopy(model.state())
                with patch('scene_tool.ui.variant_binding.show_variants') as show:
                    open_scene_variants(panel)
                choices,apply=show.call_args.args[1:]
                self.assertEqual(before,model.state())
                self.assertTrue(apply(choices[-1]))
                self.assertEqual(model.values[key],'我的自填说明')
                self.assertEqual(model.prompt,choices[-1].prompt)
                self.assertEqual(model.generate(),choices[-1].prompt)
                self.assertEqual(displayed[-1],persisted[-1]['prompt'])
                self.assertEqual(model.rng.getstate(),choices[-1].payload['rng'].getstate())


import sys
from pathlib import Path
from types import SimpleNamespace
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scene_tool.ui.prompt_reset import PromptResetController
from scene_tool.config.defaults import DEFAULT_CONSTRAINTS, DIMENSIONS
from scene_tool.config.photography import DECORATION_REQUIREMENTS


class Text:
    def __init__(self, value): self.value = value
    def get(self, *_): return self.value
    def delete(self, *_): self.value = ''
    def insert(self, _, text): self.value = text


class ResetTests(unittest.TestCase):
    def make_view(self):
        values = {key: '当前值' for key, _ in DIMENSIONS}
        view = SimpleNamespace(current=lambda: dict(values), industry=Text('美业'), copyline=Text('我的文案'),
            constraints=Text('我的固定要求'), extra=Text('我的补充'), prompt=Text('我的手改提示词'),
            rendered='之前生成内容', pending=None, status=SimpleNamespace(set=lambda _: None),
            undo_reset_button=SimpleNamespace(configure=lambda **_: None), save=lambda: True)
        def set_prompt(text):
            view.prompt.value = text
            view.rendered = text
        view.set_prompt = set_prompt
        return view

    def test_reset_and_undo_preserve_parameters(self):
        view = self.make_view()
        controller = PromptResetController(view)
        previous_values = view.current()
        self.assertTrue(controller.reset())
        self.assertEqual(view.constraints.value, DEFAULT_CONSTRAINTS)
        self.assertEqual(view.extra.value, '')
        self.assertIn(DECORATION_REQUIREMENTS, view.prompt.value)
        self.assertIn('我的文案', view.prompt.value)
        self.assertEqual(view.current(), previous_values)
        controller.reset()
        self.assertTrue(controller.undo())
        self.assertEqual(view.prompt.value, '我的手改提示词')
        self.assertEqual(view.extra.value, '我的补充')
        self.assertEqual(view.constraints.value, '我的固定要求')
        self.assertEqual(view.rendered, '之前生成内容')
        self.assertFalse(controller.undo())

    def test_invalid_parameters_do_not_destroy_text(self):
        view = self.make_view()
        view.current = lambda: {}
        self.assertFalse(PromptResetController(view).reset())
        self.assertEqual(view.prompt.value, '我的手改提示词')

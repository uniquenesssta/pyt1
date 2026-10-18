import sys
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scene_tool.ui.resize_controller import ResizeController


class ResizeTests(unittest.TestCase):
    def setUp(self):
        self.window = Mock()
        self.window.after.side_effect = ['timer1', 'timer2', 'timer3']
        self.text = Mock()
        self.text.cget.return_value = 'word'
        self.text.index.return_value = '12.0'
        self.controller = ResizeController(self.window, [self.text])
        self.event(100, 100)

    def event(self, width, height):
        self.controller.on_configure(SimpleNamespace(widget=self.window, width=width, height=height))

    def test_move_and_child_layout_do_not_trigger_reflow(self):
        self.event(100, 100)
        self.controller.on_configure(SimpleNamespace(widget=self.text, width=500, height=300))
        self.text.configure.assert_not_called()
        self.window.after.assert_not_called()

    def test_resize_burst_suspends_once_and_restores_reading_position(self):
        self.event(110, 100)
        self.event(120, 110)
        self.text.configure.assert_called_once_with(wrap='none')
        self.window.after_cancel.assert_called_once_with('timer1')
        self.controller.restore()
        self.text.configure.assert_called_with(wrap='word')
        self.text.yview.assert_called_once_with('12.0')
        self.text.delete.assert_not_called()
        self.text.insert.assert_not_called()

    def test_close_cancels_pending_callback(self):
        self.event(110, 100)
        self.controller.on_destroy(SimpleNamespace(widget=self.window))
        self.window.after_cancel.assert_called_once_with('timer1')
        self.assertIsNone(self.controller.pending)

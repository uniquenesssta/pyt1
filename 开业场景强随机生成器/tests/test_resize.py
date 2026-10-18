import sys
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scene_tool.ui.resize_controller import ResizeController


class ResizeTests(unittest.TestCase):
    def setUp(self):
        self.window = Mock()
        self.text = Mock()
        self.text.cget.return_value = 'word'
        self.text.index.return_value = '12.0'
        with patch('scene_tool.ui.resize_controller.WindowsResizeHook') as hook:
            self.controller = ResizeController(self.window, [self.text])
            self.hook = hook.return_value

    def test_pause_persists_until_explicit_end_without_timer(self):
        self.controller.pause()
        self.controller.pause()
        self.text.configure.assert_called_once_with(wrap='none')
        self.window.after.assert_not_called()
        self.controller.restore()
        self.text.configure.assert_called_with(wrap='word')
        self.text.yview.assert_called_once_with('12.0')
        self.text.delete.assert_not_called()
        self.text.insert.assert_not_called()

    def test_move_end_without_resize_does_not_touch_text(self):
        self.controller.restore()
        self.text.configure.assert_not_called()

    def test_close_cancels_install_and_removes_hook(self):
        self.controller.on_destroy(SimpleNamespace(widget=self.window))
        self.window.after_cancel.assert_called_once()
        self.hook.close.assert_called_once()

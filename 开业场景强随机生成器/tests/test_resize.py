import sys
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scene_tool.ui.resize_controller import ResizeController


class ResizeTests(unittest.TestCase):
    def setUp(self):
        self.window, self.surface = Mock(), Mock()
        self.button = Mock(return_value=True)
        self.controller = ResizeController(self.window, self.surface, self.button)
        self.event(1000, 800)

    def event(self, width, height):
        self.controller.on_configure(SimpleNamespace(widget=self.window, width=width, height=height))

    def test_hold_freezes_layout_even_during_long_pause(self):
        self.event(1100, 850)
        self.surface.place_configure.assert_called_once_with(relwidth=0, relheight=0, width=1000, height=800)
        for _ in range(100):
            self.controller.check_release()
        self.event(1200, 900)
        self.assertEqual(self.surface.place_configure.call_count, 1)
        self.button.return_value = False
        self.controller.check_release()
        self.surface.place_configure.assert_called_with(width=0, height=0, relwidth=1, relheight=1)

    def test_move_or_maximize_without_held_button_does_not_freeze(self):
        self.event(1000, 800)
        self.button.return_value = False
        self.event(1400, 1000)
        self.surface.place_configure.assert_not_called()

    def test_close_cancels_release_poll(self):
        self.event(1100, 850)
        self.controller.on_destroy(SimpleNamespace(widget=self.window))
        self.window.after_cancel.assert_called_once()
        self.assertIsNone(self.controller.pending)

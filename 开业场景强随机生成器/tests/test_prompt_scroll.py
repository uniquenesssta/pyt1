"""Scene changes share scroll progress, including unequal text lengths."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scene_tool.ui.prompt_scroll import PromptScrollMemory


class Scheduler:
    def __init__(self):
        self.jobs = {}
        self.counter = 0

    def after_idle(self, callback):
        self.counter += 1
        self.jobs[self.counter] = callback
        return self.counter

    def after_cancel(self, token):
        self.jobs.pop(token, None)

    def run(self):
        jobs, self.jobs = self.jobs, {}
        for callback in jobs.values():
            callback()


class TextView:
    def __init__(self, first, visible):
        self.first, self.visible = first, visible
        self.mapped = True

    def yview(self):
        return self.first, self.first + self.visible

    def yview_moveto(self, first):
        self.first = first

    def winfo_exists(self):
        return True

    def winfo_ismapped(self):
        return self.mapped


class ScrollTests(unittest.TestCase):
    def setUp(self):
        self.scheduler = Scheduler()
        self.memory = PromptScrollMemory(self.scheduler)

    def test_carries_midpoint_instead_of_target_previous_position(self):
        self.memory.remember(TextView(.4, .2))
        target = TextView(.0, .4)
        self.memory.restore(target)
        self.scheduler.run()
        self.assertAlmostEqual(target.first, .3)
        # The user's newly scrolled position becomes the shared position.
        target.first = .6
        self.memory.remember(target)
        previous = TextView(.4, .2)
        self.memory.restore(previous)
        self.scheduler.run()
        self.assertAlmostEqual(previous.first, .8)

    def test_bottom_and_top_with_different_document_lengths(self):
        for start, expected in ((.8, .6), (.0, .0)):
            self.memory.remember(TextView(start, .2))
            target = TextView(.1, .4)
            self.memory.restore(target)
            self.scheduler.run()
            self.assertAlmostEqual(target.first, expected)

    def test_rapid_switch_does_not_capture_unrestored_target(self):
        self.memory.remember(TextView(.4, .2))
        intermediate = TextView(0, .3)
        self.memory.restore(intermediate)
        self.memory.remember(intermediate)
        target = TextView(0, .4)
        self.memory.restore(target)
        self.scheduler.run()
        self.assertEqual(intermediate.first, 0)
        self.assertAlmostEqual(target.first, .3)

    def test_short_document_preserves_shared_scroll_progress(self):
        self.memory.remember(TextView(.8, .2))
        short = TextView(0, 1)
        self.memory.restore(short)
        self.scheduler.run()
        self.memory.remember(short)
        target = TextView(0, .3)
        self.memory.restore(target)
        self.scheduler.run()
        self.assertAlmostEqual(target.first, .7)


if __name__ == '__main__':
    unittest.main()

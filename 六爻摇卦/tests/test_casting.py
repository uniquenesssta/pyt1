"""在无显示器环境验证完整起卦、重入及定时器生命周期。"""
import heapq
import random
import unittest

from liuyao_tool.ui.casting import CastingController


class Scheduler:
    def __init__(self):
        self.now = 0
        self.sequence = 0
        self.queue = []
        self.callbacks = {}
        self.destroyed = False

    def after(self, delay, callback):
        self.sequence += 1
        token = self.sequence
        self.callbacks[token] = callback
        heapq.heappush(self.queue, (self.now + delay, token))
        return token

    def after_cancel(self, token):
        del self.callbacks[token]

    def run_all(self):
        steps = 0
        while self.queue:
            steps += 1
            if steps > 1000:
                raise AssertionError("动画未能停止")
            self.now, token = heapq.heappop(self.queue)
            callback = self.callbacks.pop(token, None)
            if callback is not None:
                callback()

    def destroy(self):
        self.destroyed = True


class View:
    def __init__(self):
        self.resets = 0
        self.results = []
        self.casting = False
        self.lines = {}

    def reset(self):
        self.resets += 1
        self.lines = {}

    def set_casting(self, value):
        self.casting = value

    def show_rolling(self, index, symbol):
        pass

    def show_line(self, index, line):
        self.lines[index] = line

    def show_result(self, result):
        self.results.append(result)


class CastingTests(unittest.TestCase):
    def setUp(self):
        self.scheduler = Scheduler()
        self.view = View()
        self.controller = CastingController(self.scheduler, self.view, random.Random(1742))

    def test_completes_six_lines_and_allows_another_cast(self):
        for cast_number in (1, 2):
            self.controller.start()
            self.assertTrue(self.view.casting)
            self.scheduler.run_all()
            self.assertFalse(self.view.casting)
            self.assertEqual(len(self.view.results), cast_number)
            self.assertEqual(len(self.view.lines), 6)
            self.assertEqual(self.view.results[-1].lines, tuple(self.view.lines[i] for i in range(6)))
            self.assertFalse(self.scheduler.callbacks)
        self.assertEqual(self.view.resets, 2)

    def test_start_during_cast_does_not_schedule_another_round(self):
        self.controller.start()
        jobs = dict(self.scheduler.callbacks)
        self.controller.start()
        self.assertEqual(self.scheduler.callbacks, jobs)
        self.assertEqual(self.view.resets, 1)
        self.scheduler.run_all()
        self.assertEqual(len(self.view.results), 1)

    def test_close_during_animation_cancels_every_callback(self):
        self.controller.start()
        self.controller.close()
        self.assertTrue(self.scheduler.destroyed)
        self.assertFalse(self.scheduler.callbacks)
        self.scheduler.run_all()
        self.assertFalse(self.view.results)
        self.controller.close()
        self.controller.start()
        self.assertFalse(self.scheduler.callbacks)

    def test_close_before_start_is_safe(self):
        self.controller.close()
        self.assertTrue(self.scheduler.destroyed)
        self.controller.start()
        self.assertEqual(self.view.resets, 0)


if __name__ == "__main__":
    unittest.main()

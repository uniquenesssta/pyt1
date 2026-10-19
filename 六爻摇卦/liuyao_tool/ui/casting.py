"""管理摇卦动画、逐爻停止与窗口关闭时的定时器清理。"""
import random

from ..domain.yao import Hexagram, YANG_SYMBOL, YIN_SYMBOL
from ..generation.coins import toss_line


class CastingController:
    def __init__(self, scheduler, view, rng=None):
        self.scheduler = scheduler
        self.view = view
        self.rng = rng if rng is not None else random.SystemRandom()
        self._casting = False
        self._closed = False
        self._active = [False] * 6
        self._animation_jobs = [None] * 6
        self._stop_jobs = [None] * 6
        self._lines = [None] * 6

    def start(self):
        if self._closed or self._casting:
            return
        self._casting = True
        self._lines = [None] * 6
        self.view.reset()
        self.view.set_casting(True)
        for index in range(6):
            self._active[index] = True
            self._animate(index)
            self._stop_jobs[index] = self.scheduler.after(
                self.rng.randint(1000, 3500),
                lambda idx=index: self._stop(idx),
            )

    def _animate(self, index):
        self._animation_jobs[index] = None
        if self._closed or not self._active[index]:
            return
        self.view.show_rolling(index, self.rng.choice((YANG_SYMBOL, YIN_SYMBOL)))
        self._animation_jobs[index] = self.scheduler.after(
            80, lambda idx=index: self._animate(idx)
        )

    def _stop(self, index):
        self._stop_jobs[index] = None
        if self._closed or not self._active[index]:
            return
        self._active[index] = False
        self._cancel(self._animation_jobs, index)
        line = toss_line(self.rng)
        self._lines[index] = line
        self.view.show_line(index, line)
        if all(line is not None for line in self._lines):
            self.view.show_result(Hexagram(tuple(self._lines)))
            self._casting = False
            self.view.set_casting(False)

    def _cancel(self, jobs, index):
        if jobs[index] is not None:
            self.scheduler.after_cancel(jobs[index])
            jobs[index] = None

    def close(self):
        if self._closed:
            return
        self._closed = True
        self._casting = False
        self._active = [False] * 6
        for index in range(6):
            self._cancel(self._animation_jobs, index)
            self._cancel(self._stop_jobs, index)
        self.scheduler.destroy()

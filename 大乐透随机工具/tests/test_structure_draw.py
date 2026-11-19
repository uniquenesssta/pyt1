"""运行真实的结构生成任务；界面可见性由 Tk 窗口测试另行验证。"""
from functools import partial
from time import monotonic, sleep
from types import SimpleNamespace
from unittest.mock import Mock
import tkinter as tk
import unittest

from lottery.core.generation import MODES
from lottery.core.models import Draw, Ticket
from lottery.core.structure_cache import StructureCache
from lottery.ui.app import LotteryApp
from lottery.ui.controls import GenerationControls
from lottery.ui.cross_link import CrossWeightLink
from lottery.ui.indicator_picker import IndicatorSelection
from lottery.ui.jobs import Jobs
from lottery.ui.selection_inputs import SelectionInputs
from lottery.ui.structure_weights import StructureWeightsPage


class StructureDrawTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tcl()
        def var(value=""):
            return tk.StringVar(self.root, value=value)

        draws = [Draw(Ticket((1, 2, 7, 18, 35) if i < 60 else (3, 5, 8, 21, 31),
                             (1, 2)), str(26001 + i)) for i in reversed(range(120))]
        errors = []
        selection = IndicatorSelection(self.root)
        selection.set(("C1差值",))
        self.page = SimpleNamespace(
            draws=draws, profile=None, period=var("50"), summary=var(), pending=var(),
            _busy=False, draw_panel=Mock(), use_button=Mock(), render=Mock(),
            error=errors.append,
            indicator_selection=selection,
        )
        for method in ("periods", "describe_pending", "describe", "rebuild", "snapshot"):
            setattr(self.page, method, partial(getattr(StructureWeightsPage, method), self.page))

        self.inputs = SelectionInputs(self.root)
        controls = SimpleNamespace(
            inputs=self.inputs, mode=var(MODES[0]), fill_button=Mock(),
            custom=tk.BooleanVar(self.root, value=False), cross_source=var(),
            weight_vars=[[var("1") for _ in range(5)] for _ in range(2)],
        )
        controls.snapshot = partial(GenerationControls.snapshot, controls)
        link = CrossWeightLink(controls, self.page, errors.append)
        results, statuses = [], []
        self.app = SimpleNamespace(
            controls=controls, structure_weights=self.page, cross_link=link,
            structure_cache=StructureCache(), stats=None,
            generated=SimpleNamespace(set_tickets=results.append), results_tabs=Mock(),
            show_structure_selection=Mock(), set_status=statuses.append, error=errors.append,
            jobs=Jobs(self.root, statuses.append, lambda busy: None),
            indicator_selection=selection,
        )
        self.app.generate = partial(LotteryApp.generate, self.app)
        self.draw = partial(LotteryApp.draw_from_structure, self.app)
        self.addCleanup(self.app.jobs.close)
        self.results, self.statuses, self.errors = results, statuses, errors
        self.page.rebuild()
        self.assertEqual(self.errors, [])

    def finish(self):
        deadline = monotonic() + 5
        while self.app.jobs.running and monotonic() < deadline:
            self.root.update()
            sleep(.01)
        self.assertFalse(self.app.jobs.running, "结构抽取后台任务超时")

    def test_draw_with_applied_window_edits_and_shared_number_inputs(self):
        self.page.period.set("100")
        self.page.rebuild()
        profile = self.page.profile
        self.assertEqual(profile.counts["C1差值"][1], 40)
        self.assertEqual(profile.means["C1差值"], 1.6)
        self.assertIn("26021 → 26120", self.page.summary.get())
        # 两个前区候选仅差一个号码：C1 权重为 0 的候选不得入选。
        allowed = {2, 5, 6, 12, 19, 26}
        for name, value in {
            "组数": "4", "前区数量": "8", "后区数量": "3",
            "前区固定": "06 12 19 26", "后区固定": "01", "后区排除": "12",
            "前区排除": " ".join(str(n) for n in range(1, 36) if n not in allowed),
        }.items():
            self.inputs.values[name].set(value)
        profile.weights["C1差值"] = {k: float(k == 1) for k in profile.weights["C1差值"]}
        self.draw()
        self.finish()

        self.assertEqual(self.errors, [])
        self.assertEqual(len(set(self.results[0])), 4)
        for ticket in self.results[0]:
            self.assertEqual(ticket.front, (5, 6, 12, 19, 26))
            self.assertEqual(len(ticket.back), 3)
            self.assertIn(1, ticket.back)
            self.assertNotIn(12, ticket.back)
        self.assertIn("历史结构加权 · 实际使用 100 期（26021–26120）", self.statuses[-1])
        self.app.show_structure_selection.assert_called_once_with()
        self.assertIs(self.page.profile, profile)

    def test_unapplied_period_cannot_start_a_draw(self):
        previous = self.page.profile
        self.page.period.set("17")
        self.draw()
        self.assertFalse(self.app.jobs.running)
        self.assertEqual(self.results, [])
        self.assertIn("期数已修改", str(self.errors[0]))
        self.assertIs(self.page.profile, previous)

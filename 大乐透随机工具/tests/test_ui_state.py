"""用真实 Tcl 变量验证页面状态；不将其当作实际窗口测试。"""
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock
import tkinter as tk
import unittest
from lottery.core.models import Draw, Ticket
from lottery.core.structure_profile import build_profile, domains
from lottery.ui.hot_cold import HotColdPanel
from lottery.ui.structure_weights import StructureWeightsPage, GROUPS


class PageStateTests(unittest.TestCase):
    def setUp(self):
        self.tcl = tk.Tcl()
        self.draws = [Draw(Ticket((1, 2, 3, 4, 5) if i < 60 else (6, 7, 8, 9, 10), (1, 2)),
                           str(26001 + i)) for i in range(120)]

    def var(self, text=''):
        return tk.StringVar(master=self.tcl, value=text)

    def hot_panel(self):
        panel = SimpleNamespace(draws=[], main_periods=0, period=self.var('跟随统计范围'),
            report=None, summary=self.var(), rule=self.var(), tables={'前区': Mock(), '后区': Mock()}, on_open=Mock())
        panel.selected_periods = lambda: HotColdPanel.selected_periods(panel)
        panel.refresh = lambda: HotColdPanel.refresh(panel)
        return panel

    def test_follow_override_and_return_follow(self):
        panel = self.hot_panel()
        HotColdPanel.follow_scope(panel, 50, self.draws)
        self.assertEqual(panel.report.total, 50)
        panel.period.set('近100期')
        panel.refresh()
        HotColdPanel.follow_scope(panel, 0)
        self.assertEqual(panel.report.total, 100)
        self.assertIn('独立对比', panel.summary.get())
        HotColdPanel.open_number(panel, '前区', panel.report.front[0])
        self.assertEqual(panel.on_open.call_args.args[2], 100)
        panel.period.set('跟随统计范围')
        panel.refresh()
        self.assertEqual(panel.report.total, 120)
        HotColdPanel.open_number(panel, '前区', panel.report.front[0])
        self.assertEqual(panel.on_open.call_args.args[2], 0)

    def test_replacing_history_and_failure_do_not_keep_old_hot_numbers(self):
        panel = self.hot_panel()
        HotColdPanel.follow_scope(panel, 50, self.draws)
        new = self.draws[:3]
        HotColdPanel.follow_scope(panel, 50, new)
        self.assertEqual(panel.report.total, 3)
        conflict = Draw(Ticket((6, 7, 8, 9, 10), (1, 2)), new[0].issue)
        HotColdPanel.follow_scope(panel, 50, new + [conflict])
        self.assertIsNone(panel.report)
        for table in panel.tables.values():
            table.set_rows.assert_called_with([])

    def test_structure_groups_cover_each_existing_metric_once(self):
        names = [name for group in GROUPS.values() for name in group]
        self.assertEqual(set(names), set(domains()))
        self.assertEqual(len(names), len(set(names)))

    def test_restore_only_selected_group_and_preserve_strength(self):
        original = build_profile(self.draws, 50)
        edited = deepcopy(original)
        edited.weights['C1差值'][1] = 75
        edited.weights['C2差值'][2] = 60
        edited.strengths['C1差值'] = 3
        page = SimpleNamespace(profile=edited, group=self.var('C1差值'), render=Mock(), on_change=Mock())
        StructureWeightsPage.restore_group(page)
        self.assertEqual(page.profile.weights['C1差值'], original.weights['C1差值'])
        self.assertEqual(page.profile.weights['C2差值'][2], 60)
        self.assertEqual(page.profile.strengths['C1差值'], 3)
        self.assertEqual(edited.weights['C1差值'][1], 75)
        page.on_change.assert_called_once_with(page.profile)

    def test_unapplied_period_preserves_profile_and_blocks_generation(self):
        profile = build_profile(self.draws, 50)
        page = SimpleNamespace(profile=profile, period=self.var('100'), pending=self.var())
        page.periods = lambda: StructureWeightsPage.periods(page)
        StructureWeightsPage.describe_pending(page)
        self.assertIn('尚未应用', page.pending.get())
        self.assertIs(page.profile, profile)
        with self.assertRaisesRegex(ValueError, '期数已修改'):
            StructureWeightsPage.snapshot(page)

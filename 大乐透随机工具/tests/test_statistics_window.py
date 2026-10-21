import unittest
from types import SimpleNamespace
from unittest.mock import Mock
import tkinter as tk
from lottery.core.models import Draw,Ticket
from lottery.core.statistics_window import window_statistics
from lottery.core.statistics import report_rows
from lottery.core.querying import Query
from lottery.core.history_drilldown import query_history,StatisticFilter
from lottery.ui.statistics import StatisticsPage


class StatisticsWindowTests(unittest.TestCase):
    def setUp(self):
        self.draws=[Draw(Ticket((1,2,3,4,5) if i<=50 else (6,7,8,9,10),(1,2)),str(26000+i)) for i in range(1,121)]

    def test_ranges_counts_and_chart_data(self):
        for periods,total,ones in [(50,50,0),(100,100,30),(0,120,50)]:
            stats,caption=window_statistics(self.draws[::-1],periods)
            self.assertEqual(stats.total,total)
            self.assertEqual(stats.front[1],ones)
            self.assertEqual(sum(stats.front.values()),total*5)
            self.assertEqual(sum(stats.back.values()),total*2)

    def test_every_statistic_reconciles_with_click_scope(self):
        for periods in (50,100,0):
            stats,_=window_statistics(self.draws,periods)
            for category,item,count,_,_ in report_rows(stats):
                actual=query_history(self.draws,Query(),periods,StatisticFilter('统计分析',category,item))[2]
                self.assertEqual(actual,count,(periods,category,item))

    def test_short_duplicates_empty_and_invalid(self):
        draws=[self.draws[0]]*2
        self.assertEqual(window_statistics(draws,50)[0].total,1)
        self.assertEqual(window_statistics(draws,0)[0].total,2)
        self.assertEqual(window_statistics([],100)[0].total,0)
        with self.assertRaises(ValueError):window_statistics(self.draws,17)

    def test_ui_scope_updates_linked_hot_cold(self):
        interp=tk.Tcl()
        page=SimpleNamespace(draws=self.draws,scope=tk.StringVar(master=interp,value='近50期'),
                             scope_summary=tk.StringVar(master=interp),set_statistics=Mock(),
                             hot_cold=Mock(),error=Mock(),update_scope_buttons=Mock())
        StatisticsPage.refresh_scope(page)
        self.assertEqual(page.active_periods,50)
        self.assertEqual(page.set_statistics.call_args.args[0].total,50)
        page.hot_cold.follow_scope.assert_called_once_with(50,self.draws)
        page.scope.set('近100期');StatisticsPage.refresh_scope(page)
        self.assertEqual(page.active_periods,100)
        self.assertEqual(page.set_statistics.call_args.args[0].total,100)
        page.hot_cold.follow_scope.assert_called_with(100,self.draws)

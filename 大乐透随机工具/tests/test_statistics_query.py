import unittest
from lottery.core.features import features
from lottery.core.statistics import analyze, report_rows
from lottery.core.querying import search, Query
from lottery.data.importing import parse_text


class StatisticsTests(unittest.TestCase):
    def setUp(self):
        # 明确为合成测试数据，不作为应用内历史数据提供。
        self.draws = parse_text('2026001 1 2 3 22 35 1 12\n2026002 8 10 12 14 16 2 3').draws

    def test_counts_and_denominators(self):
        stats = analyze(self.draws)
        self.assertEqual(stats.total, 2)
        self.assertEqual(sum(stats.front.values()), 10)
        self.assertEqual(sum(stats.back.values()), 4)
        self.assertEqual(stats.pairs[(1, 12)], 1)
        rows = report_rows(stats)
        self.assertIn(('前区·期数占比', '01', 1, 2, 50.0), rows)
        self.assertIn(('前区·号码频率', '01', 1, 10, 10.0), rows)
        self.assertIn(('前区·号码频率', '34', 0, 10, 0.0), rows)

    def test_features_hand_calculated(self):
        f = features((35, 22, 3, 2, 1))
        self.assertEqual(f.gaps, (1, 1, 19, 13))
        self.assertEqual(f.max_span, 3)
        self.assertEqual(f.start_span, 0)
        self.assertEqual(f.longest_run, 3)
        self.assertEqual(f.empty_zones, (2, 3))
        self.assertEqual(f.intermediate_zones, (2, 3))

    def test_separate_empty_and_intermediate(self):
        f = features((8, 9, 10, 11, 12))
        self.assertEqual(f.empty_zones, (1, 3, 4, 5))
        self.assertEqual(f.intermediate_zones, ())
        self.assertEqual(f.start_span, 1)
        self.assertEqual(f.max_span, 0)
        self.assertEqual(f.longest_run, 5)

    def test_empty_statistics(self):
        self.assertTrue(all(r[-1] == 0 for r in report_rows(analyze([]))))

    def test_area_and_leading_zero(self):
        front = search(self.draws, Query('12', area='前区', mode='包含任意'))
        back = search(self.draws, Query('12', area='后区', mode='包含任意'))
        self.assertEqual(front[0][0].issue, '2026002')
        self.assertEqual(back[0][0].issue, '2026001')
        self.assertEqual(len(search(self.draws, Query('01'))), 1)

    def test_contiguous_does_not_cross_areas_or_substring(self):
        self.assertEqual(search(self.draws, Query('35 1', mode='连续位置')), [])
        self.assertEqual(len(search(self.draws, Query('1 2', area='前区', mode='连续位置'))), 1)
        self.assertEqual(search([self.draws[1]], Query('1', area='前区')), [])

    def test_all_any_and_issue_modes(self):
        self.assertEqual(len(search(self.draws, Query('1 8', mode='包含任意'))), 2)
        self.assertEqual(search(self.draws, Query('1 8', mode='包含全部')), [])
        self.assertEqual(len(search(self.draws, Query('001', '期号', mode='后三位'))), 1)
        self.assertEqual(len(search(self.draws, Query('2026', '期号', mode='前缀'))), 2)
        self.assertEqual(search(self.draws, Query('2026', '期号', mode='完全一致')), [])
        with self.assertRaises(ValueError):
            search(self.draws, Query('01', '期号', mode='后三位'))

    def test_bad_query_not_silently_accepted(self):
        with self.assertRaises(ValueError):
            search(self.draws, Query('1.5'))
        with self.assertRaises(ValueError):
            search(self.draws, Query('13', area='后区'))

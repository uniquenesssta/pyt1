"""条件频次严格使用相邻期，报表权重可独立用于实际生成。"""
from random import Random
import unittest

from lottery.core.conditional_frequency import analyze_conditional_frequency, conditional_weights
from lottery.core.generation import GenerationConfig, MODES, generate
from lottery.core.models import Draw, Ticket


class ConditionalFrequencyTests(unittest.TestCase):
    def setUp(self):
        self.draws = [Draw(Ticket(front, back), issue) for issue, front, back in (
            ("26125", (1, 2, 3, 4, 5), (4, 7)),
            ("26126", (9, 10, 11, 12, 13), (4, 8)),
            ("26128", (1, 6, 7, 8, 9), (4, 7)),
            ("26130", (2, 6, 14, 15, 16), (7, 8)),
            ("26131", (1, 2, 3, 4, 5), (4, 7)),
            ("26132", (30, 31, 32, 33, 34), (11, 12)),
        )]

    def test_exact_condition_does_not_cross_gap_or_use_future(self):
        report = analyze_conditional_frequency(self.draws[::-1], "2026131")
        self.assertEqual((report.anchor.issue, report.first_issue, report.history_count), ("26131", "26125", 5))
        one = report.front[0]
        self.assertEqual((one.occurrences, one.samples, one.top), (3, 1, (9, 10, 11, 12, 13)))
        self.assertEqual((one.counts[2], one.counts[9], one.counts[34]), (0, 1, 0))
        self.assertEqual(report.votes[9], 4)
        self.assertEqual(report.front[1].samples, 2)
        pair = report.back
        self.assertEqual((pair.condition, pair.occurrences, pair.samples, pair.top), ((4, 7), 3, 1, (4, 8)))

    def test_short_scope_and_independent_zone_flags(self):
        report = analyze_conditional_frequency(self.draws, "26131", 3)
        self.assertEqual(report.first_issue, "26128")
        self.assertEqual((report.back.occurrences, report.back.samples), (2, 0))
        with self.assertRaisesRegex(ValueError, "整对没有可用"):
            conditional_weights(report)
        front, back = conditional_weights(report, use_back=False)
        self.assertEqual((front[1], front[6], set(back.values())), (2, 1, {1}))
        with self.assertRaisesRegex(ValueError, "请选择"):
            conditional_weights(report, False, False)

    def test_conditional_weights_affect_actual_sampling(self):
        report = analyze_conditional_frequency(self.draws, "26131")
        weights = conditional_weights(report, use_front=False)
        self.assertEqual((set(weights[0].values()), weights[1][8], weights[1][12]), ({1}, 2, 1))
        config = GenerationConfig(count=600, mode=MODES[1], unique=False, back_fixed=(4,),
                                  back_excluded=tuple(n for n in range(1, 13) if n not in (4, 8, 12)))
        tickets = generate(config, rng=Random(29), frequency_weights=weights)
        count = sum(t.back == (4, 8) for t in tickets)
        self.assertGreater(count, 350)
        self.assertLess(count, 450)

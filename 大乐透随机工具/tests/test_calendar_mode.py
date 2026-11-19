"""同星期及历年同期选择真实的历史范围，输出可按档缩小。"""
from random import Random
import unittest

from lottery.core.calendar_generation import generate_calendar_set
from lottery.core.calendar_samples import CalendarRequest, select_calendar_samples
from lottery.core.generation import GenerationConfig
from lottery.core.models import Draw, Ticket


class CalendarModeTests(unittest.TestCase):
    def setUp(self):
        self.draws = [
            Draw(Ticket((1, 3, 8, 17, 32), (4, 7)), issue, draw_date=day)
            for issue, day in (
                ("24132", "2024-11-13"), ("25132", "2025-11-12"),
                ("25133", "2025-11-15"), ("26126", "2026-11-04"),
                ("26129", "2026-11-11"), ("2026132", "2026-11-18"),
                ("26133", "2026-11-21"), ("26134", "2026-11-23"),
            )
        ]

    def test_target_excluded_and_overlap_counted_once(self):
        samples = select_calendar_samples(self.draws[::-1], CalendarRequest("26132", recent_days=3, past_years=2))
        self.assertEqual((samples.target_issue, samples.weekday, samples.estimated), ("26132", 2, False))
        self.assertEqual([draw.issue for draw in samples.same_weekday], ["25132", "26126", "26129"])
        self.assertEqual([draw.issue for draw in samples.same_ordinal], ["24132", "25132"])
        self.assertEqual([draw.issue for draw in samples.draws], ["24132", "25132", "26126", "26129"])

    def test_default_uses_next_regular_draw_and_accepts_one_scope(self):
        samples = select_calendar_samples(self.draws[:6], CalendarRequest(past_years=0))
        self.assertEqual((samples.target_issue, samples.weekday, samples.estimated), ("26133", 5, True))
        self.assertEqual([draw.issue for draw in samples.draws], ["25133"])
        with self.assertRaisesRegex(ValueError, "实际开奖"):
            select_calendar_samples(self.draws, CalendarRequest("26132", weekday=5))
        with self.assertRaisesRegex(ValueError, "没有.*历年同期"):
            select_calendar_samples(self.draws[3:], CalendarRequest("26132"))

    def test_nested_sizes_and_existing_number_constraints(self):
        samples = select_calendar_samples(self.draws, CalendarRequest("26132"))
        config = GenerationConfig(front_fixed=(1, 3, 8), back_fixed=(4,),
                                  front_excluded=(35,), back_excluded=(12,))
        large, small, single = generate_calendar_set(config, samples, rng=Random(2026))
        self.assertEqual([(len(t.front), len(t.back), t.bets) for t in (large, small, single)],
                         [(15, 5, 30030), (9, 3, 378), (5, 2, 1)])
        for tickets in ((large.front, small.front, single.front), (large.back, small.back, single.back)):
            self.assertGreater(set(tickets[0]), set(tickets[1]))
            self.assertGreater(set(tickets[1]), set(tickets[2]))
        self.assertTrue({1, 3, 8} <= set(single.front))
        self.assertIn(4, single.back)
        self.assertNotIn(35, large.front)
        self.assertNotIn(12, large.back)
        with self.assertRaisesRegex(ValueError, r"后区.*不足 5.*15\+5"):
            generate_calendar_set(GenerationConfig(back_excluded=tuple(range(5, 13))), samples)

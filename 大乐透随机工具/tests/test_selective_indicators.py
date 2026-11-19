"""从期号、统计口径到实际抽取，验证新增指标和显式选择。"""
from collections import Counter
from dataclasses import replace
from random import Random
import unittest

from lottery.core.generation import GenerationConfig, MODES, generate
from lottery.core.history_drilldown import StatisticFilter, query_history
from lottery.core.models import Draw, Ticket
from lottery.core.omission import omission_report
from lottery.core.period_context import consecutive, scoped_references
from lottery.core.querying import Query
from lottery.core.structure_cache import StructureCache
from lottery.core.structure_profile import build_profile, indicator_value
from lottery.core.structure_scoring import StructureScorer


A = Ticket((1, 4, 8, 20, 35), (1, 12))
B = Ticket((1, 2, 4, 5, 28), (2, 12))


def draws_through(last):
    return [Draw(A if n % 2 else B, str(26000 + n)) for n in range(1, last + 1)]


class TemporalStructureTests(unittest.TestCase):
    def test_transitions_are_distinct_and_counted_before_text_filter(self):
        draws = [Draw(A, "26001"), Draw(B, "2026002"), Draw(A, "26004"), Draw(B, "26005")]
        selected, _, references, last = scoped_references(draws[::-1], 3)
        self.assertEqual(set(references), {draws[1], draws[-1]})
        values = [indicator_value(f"前区{name}号数", draws[1], references[draws[1]])
                  for name in ("重", "邻", "孤")]
        self.assertEqual(values, [2, 2, 1])
        self.assertEqual(last.issue, "26005")
        self.assertEqual(selected, draws[1:])
        profile = build_profile(draws, 3)
        self.assertEqual(profile.samples("前区重号数"), 2)
        self.assertEqual(profile.counts["前区重号数"][2], 2)
        self.assertAlmostEqual(sum(profile.baseline("后区邻号数").values()), 1)
        query = Query("26005", "期号", "全部", "完全一致")
        rows, total, count, _ = query_history(draws, query, 3, StatisticFilter("结构权重", "前区邻号数", "2"))
        self.assertEqual((total, count), (2, 1))
        self.assertIn("参照上一期 26004", rows[0][1])

    def test_year_boundary_compares_only_with_corroborating_dates(self):
        old = Draw(A, "25150", draw_date="2025-12-31")
        new = Draw(B, "26001", draw_date="2026-01-03")
        self.assertTrue(consecutive(old, new))
        self.assertFalse(consecutive(old, replace(new, draw_date="2026-01-05")))
        self.assertFalse(consecutive(old, replace(new, draw_date="")))

    def test_omission_sees_12_prior_draws_and_resets_at_gap(self):
        draws = [Draw(A if n == 1 else B, str(26000 + n)) for n in range(1, 15)]
        selected, _, references, forecast = scoped_references(draws, 2)
        self.assertEqual(selected, draws[-2:])
        self.assertEqual(references[draws[-2]].front.omission[35], 2)  # 11 期
        self.assertEqual(references[draws[-1]].front.omission[35], 3)  # 12 期
        self.assertEqual(forecast.front.omission[1], 0)
        profile = build_profile(draws, 2)
        self.assertEqual(profile.samples("前区遗漏结构"), 2)
        profile.validate(("前区遗漏结构",))
        draws.append(Draw(B, "26016"))
        profile = build_profile(draws, 3)
        self.assertEqual(profile.samples("前区遗漏结构"), 2)
        with self.assertRaisesRegex(ValueError, "连续"):
            profile.validate(("前区遗漏结构",))
        profile.validate(("前区和值",))
        front, _, _, last_streak, issue = omission_report(draws, 0)
        self.assertEqual((last_streak, issue), (1, "26016"))
        self.assertEqual((front[34].current, front[34].lower_bound), (1, True))
        self.assertEqual((front[0].current, front[0].max_finished), (0, 0))
        self.assertEqual(front[0].intervals, 13)  # 缺的 26015 不计作间隔

    def test_repeat_weight_uses_newest_real_reference(self):
        profile = build_profile(draws_through(20), 5)
        metric = "前区重号数"
        profile.weights[metric] = {k: float(k == 5) for k in profile.weights[metric]}
        config = GenerationConfig(count=8, mode=MODES[2], front_fixed=B.front[:4],
                                  structure_profile=profile, indicators=(metric,))
        self.assertTrue(all(t.front == B.front for t in generate(config, rng=Random(9))))

    def test_back_omission_shape_filters_actual_pairs(self):
        profile = build_profile(draws_through(20), 10)
        metric = "后区遗漏结构"
        # 末期 B 中 02/12 为当前 0 期，01 缺 1 期，其余号连续 12 期以上。
        shape = "0:1:0:1"
        profile.weights[metric] = {k: float(k == shape) for k in profile.weights[metric]}
        config = GenerationConfig(count=8, mode=MODES[2], front_fixed=A.front,
                                  structure_profile=profile, indicators=(metric,))
        tickets = generate(config, rng=Random(35))
        self.assertEqual(len(set(tickets)), 8)
        self.assertTrue(all(t.back[0] == 1 and 3 <= t.back[1] <= 11 for t in tickets))


class SelectiveWeightTests(unittest.TestCase):
    def setUp(self):
        self.profile = build_profile(draws_through(20), 10)

    def test_selected_metrics_multiply_and_single_strength_changes_ratio(self):
        p = self.profile
        first, second = (1, 2, 8, 19, 30), (1, 3, 8, 19, 30)
        p.weights["C1差值"].update({1: 100, 2: 50})
        p.strengths["C1差值"] = 2
        p.weights["前区和值"].update({60: 50, 61: 25})
        p.weights["前区同尾组数"] = dict.fromkeys(p.weights["前区同尾组数"], 0)
        single = StructureScorer(p, ("C1差值",))
        multi = StructureScorer(p, ("C1差值", "前区和值"))
        self.assertAlmostEqual(single.weight(first) / single.weight(second), 4)
        self.assertAlmostEqual(multi.weight(first) / multi.weight(second), 8)
        with self.assertRaisesRegex(ValueError, "所有类别"):
            StructureScorer(p, ("前区同尾组数",))

    def test_unselected_back_uses_no_frequency_bias(self):
        draws = [Draw(A, str(26000+n)) for n in range(1, 81)]
        profile = build_profile(draws, 50)
        config = GenerationConfig(mode=MODES[2], structure_profile=profile, indicators=("前区和值",),
                                  count=2000, unique=False, front_fixed=A.front, back_fixed=(1,),
                                  back_excluded=tuple(range(3, 12)))
        picks = Counter(t.back for t in generate(config, rng=Random(137)))
        self.assertAlmostEqual(picks[(1, 12)] / 2000, .5, delta=.05)
        with self.assertRaisesRegex(ValueError, "选择"):
            generate(replace(config, indicators=()))
        profile.strengths["前区和值"] = 0
        with self.assertRaisesRegex(ValueError, "强度"):
            generate(config)

    def test_only_selected_front_edits_invalidate_cache(self):
        p = self.profile
        config = GenerationConfig(mode=MODES[2], structure_profile=p, indicators=("C1差值",),
                                  front_fixed=A.front[:4])
        cache = StructureCache()
        before = generate(config, rng=Random(10), structure_cache=cache)
        p.weights["前区第1位"][1] = 0
        after = generate(config, rng=Random(10), structure_cache=cache)
        self.assertEqual(before, after)
        self.assertEqual((cache.builds, cache.hits), (1, 1))
        chosen = replace(config, indicators=("前区第1位",))
        with self.assertRaisesRegex(ValueError, "没有可用"):
            generate(chosen, structure_cache=cache)

"""验证走势图指标的口径、均匀基准及前后区真实抽取。"""
from collections import Counter
from copy import deepcopy
from dataclasses import replace
from itertools import combinations
from math import comb
from random import Random
import unittest

from lottery.core.generation import GenerationConfig, MODES, generate
from lottery.core.models import Draw, Ticket
from lottery.core.structure_cache import StructureCache
from lottery.core.structure_profile import build_profile, structure_values
from lottery.core.trend_baseline import trend_suggestions, uniform_fractions
from lottery.core.trend_indicators import BACK, TREND_INDICATORS, trend_values


SAMPLE = Ticket((2, 9, 16, 26, 35), (6, 11))


def limit_to(profile, name, categories):
    profile.strengths[name] = 1
    profile.weights[name] = {key: 100.0 if key in categories else 0.0 for key in profile.weights[name]}


class TrendStructureTests(unittest.TestCase):
    def setUp(self):
        self.profile = build_profile([Draw(SAMPLE, "26132")])
        self.config = GenerationConfig(mode=MODES[2], structure_profile=self.profile,
                                       front_fixed=(2, 9, 16, 26), indicators=("C1差值",))

    def test_draw_shapes_keep_both_zones_separate(self):
        values = structure_values(SAMPLE.front, SAMPLE.back)
        expected = {
            "前区和值": 88, "前区跨度": 33, "前区奇偶比": "2:3",
            "前区小大比": "3:2", "前区012路比": "1:1:3",
            "后区和值": 17, "后区跨度": 5, "后区奇偶比": "1:1",
            "后区小大比": "1:1", "后区012路比": "1:0:1",
            "前区同尾组数": 1, "后区同尾组数": 0,
            "前区质合比": "1:4:0", "后区质合比": "1:1:0",
            "前区三区比": "2:1:2", "前区五区比": "1:1:1:1:1", "后区三区比": "0:1:1",
            "前区AC值": 5,
            "前区第1位": 2, "前区第2位": 9, "前区第3位": 16, "前区第4位": 26, "前区第5位": 35,
            "后区第1位": 6, "后区第2位": 11,
        }
        self.assertEqual({name: values[name] for name in TREND_INDICATORS}, expected)
        self.assertEqual(sum(values[f"C{i}差值"] for i in range(1, 5)), values["前区跨度"])

    def test_theoretical_baseline_against_back_pool_and_front_extremes(self):
        totals = {name: Counter() for name, indicator in TREND_INDICATORS.items() if indicator.zone == BACK}
        for pair in combinations(range(1, 13), 2):
            for name, value in trend_values(pair, BACK).items():
                totals[name][value] += 1
        for name in TREND_INDICATORS:
            distribution = uniform_fractions(name)
            self.assertAlmostEqual(sum(distribution.values()), 1)
            if name in totals:
                self.assertEqual(distribution, {key: count / 66 for key, count in totals[name].items()})
        self.assertEqual(uniform_fractions("前区和值")[15], 1 / comb(35, 5))
        self.assertEqual(uniform_fractions("前区和值")[165], 1 / comb(35, 5))
        self.assertEqual(uniform_fractions("前区跨度")[4], 31 / comb(35, 5))
        self.assertEqual(uniform_fractions("前区奇偶比")["3:2"], comb(18, 3)*comb(17, 2)/comb(35, 5))

    def test_recent_windows_fill_means_and_baseline_corrected_suggestions(self):
        older = Ticket((1, 2, 3, 4, 5), (1, 2))
        draws = [Draw(older if number <= 50 else SAMPLE, str(26000 + number))
                 for number in reversed(range(1, 101))]
        for window, expected in ((50, 88), (100, 51.5), (17, 88)):
            p = build_profile(draws, window)
            self.assertEqual(p.means["前区和值"], expected)
            self.assertEqual(sum(p.counts["后区小大比"].values()), window)
            self.assertEqual(p.means["前区奇偶比"], (2, 3) if window != 100 else (2.5, 2.5))
            self.assertEqual(p.weights["前区和值"], p.suggested_weights("前区和值"))
        theory = uniform_fractions("前区小大比")
        neutral = trend_suggestions("前区小大比", {k: 100*p for k,p in theory.items()}, 100)
        self.assertTrue(all(value == 50 for value in neutral.values()))
        self.assertLess(trend_suggestions("前区小大比", Counter(), 50)["0:5"], 50)

    def test_new_groups_do_not_change_generation_until_enabled(self):
        self.assertTrue(all(self.profile.strengths[name] == 1 for name in TREND_INDICATORS))
        edited = deepcopy(self.profile)
        for name in TREND_INDICATORS:
            edited.weights[name] = dict.fromkeys(edited.weights[name], 0.0)
        config = replace(self.config, count=20)
        self.assertEqual(generate(config, rng=Random(9)),
                         generate(replace(config, structure_profile=edited), rng=Random(9)))

    def test_front_sum_and_back_parity_both_reach_actual_sampling(self):
        limit_to(self.profile, "前区和值", {88})
        limit_to(self.profile, "后区奇偶比", {"1:1"})
        config = replace(self.config, indicators=("前区和值", "后区奇偶比"))
        for unique in (True, False):
            tickets = generate(replace(config, count=6, unique=unique, back_fixed=(6,)), rng=Random(4))
            self.assertEqual(len(tickets), 6)
            self.assertTrue(all(t.front == SAMPLE.front and 6 in t.back and sum(n % 2 for n in t.back) == 1
                                for t in tickets))
            if unique:
                self.assertEqual(len(set(tickets)), 6)

    def test_back_compound_scores_each_pair_and_reuses_front_cache(self):
        cache = StructureCache()
        config = replace(self.config, back_count=3, back_fixed=(6,), count=12)
        generate(config, rng=Random(1), structure_cache=cache)
        limit_to(self.profile, "后区跨度", {2, 4})
        config = replace(config, indicators=config.indicators + ("后区跨度",))
        tickets = generate(config, rng=Random(1), structure_cache=cache)
        self.assertEqual((cache.builds, cache.hits), (1, 1))
        self.assertTrue(all(6 in t.back and all(b - a in (2, 4) for a, b in combinations(t.back, 2))
                            for t in tickets))
        limit_to(self.profile, "后区奇偶比", {"1:1"})
        with self.assertRaisesRegex(ValueError, "没有可用的后区组合"):
            generate(replace(config, indicators=config.indicators + ("后区奇偶比",)), structure_cache=cache)

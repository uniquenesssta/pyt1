from collections import Counter
from dataclasses import replace
from itertools import combinations
from math import comb
import random
from threading import Event
import unittest
from lottery.core.generation import GenerationConfig, MODES, generate, unrank_combination
from lottery.core.models import Ticket, Cancelled
from lottery.core.statistics import analyze
from lottery.core.features import features
from lottery.core.selection import subset_probability
from lottery.core.weighted import weighted_sample
from lottery.data.importing import parse_text


class GenerationTests(unittest.TestCase):
    def setUp(self):
        self.rng = random.Random(42)  # 仅测试注入；产品默认 SystemRandom，无可设置种子。
        self.stats = analyze(parse_text('1 2 3 4 5 1 2\n8 11 19 25 32 5 10').draws)

    def test_uniform_range_uniqueness_and_batch(self):
        tickets = generate(GenerationConfig(count=10000), rng=self.rng)
        self.assertEqual(len(set(tickets)), 10000)
        self.assertTrue(all(len(t.front) == 5 and len(t.back) == 2 for t in tickets))

    def test_unranking_exhaustive(self):
        for n in range(1, 10):
            for k in range(n+1):
                pool = tuple(range(1, n+1))
                actual = [unrank_combination(pool, k, r) for r in range(comb(n, k))]
                self.assertEqual(actual, list(combinations(pool, k)))

    def test_fixed_excluded_all_modes(self):
        for mode in MODES:
            config = GenerationConfig(count=20, front_fixed=(1, 3), back_fixed=(2,),
                                      front_excluded=(4, 7), back_excluded=(1, 12), mode=mode)
            tickets = generate(config, self.stats, rng=self.rng)
            self.assertEqual(len(set(tickets)), 20)
            for t in tickets:
                self.assertTrue({1, 3} <= set(t.front))
                self.assertIn(2, t.back)
                self.assertFalse({4, 7} & set(t.front))
                self.assertFalse({1, 12} & set(t.back))

    def test_small_space_exhaustion_and_overflow(self):
        cfg = GenerationConfig(count=3, front_fixed=(1, 2, 3, 4, 5), back_fixed=(1,), back_excluded=tuple(range(5, 13)))
        for mode in MODES:
            result = generate(replace(cfg, mode=mode), self.stats, rng=self.rng)
            self.assertEqual({t.back for t in result}, {(1, 2), (1, 3), (1, 4)})
        with self.assertRaisesRegex(ValueError, '最多 3'):
            generate(replace(cfg, count=4))

    def test_all_fixed_and_duplicates_allowed(self):
        cfg = GenerationConfig(count=10, front_fixed=(1, 2, 3, 4, 5), back_fixed=(1, 2), unique=False)
        for mode in MODES:
            result = generate(replace(cfg, mode=mode), self.stats, rng=self.rng)
            self.assertEqual(len(result), 10)
            self.assertEqual(len(set(result)), 1)

    def test_compound_counts_and_price(self):
        for mode in MODES[:2]:
            tickets = generate(GenerationConfig(count=10, front_count=34, back_count=12, mode=mode), self.stats, rng=self.rng)
            self.assertTrue(all(len(t.front) == 34 and len(t.back) == 12 for t in tickets))
        self.assertEqual(Ticket(tuple(range(1, 13)), (1, 2)).bets * 2, 1584)
        ticket = Ticket(tuple(range(1, 16)), (1, 2, 3))
        self.assertEqual((ticket.bets*2, ticket.bets*3), (18018, 27027))

    def test_undefined_history_not_silently_uniform(self):
        for mode in MODES[1:]:
            with self.assertRaisesRegex(ValueError, '导入'):
                generate(GenerationConfig(mode=mode))

    def test_input_errors(self):
        configs = [GenerationConfig(count=0), GenerationConfig(count=-1), GenerationConfig(count=10001),
                   GenerationConfig(front_count=4), GenerationConfig(back_count=13), GenerationConfig(front_fixed=(1,1)),
                   GenerationConfig(front_fixed=(1,), front_excluded=(1,)), GenerationConfig(front_excluded=tuple(range(1,33))),
                   GenerationConfig(mode=MODES[2], front_count=6), GenerationConfig(mode='bad'),
                   GenerationConfig(mode=MODES[2], max_span_weights=(0,)*5),
                   GenerationConfig(mode=MODES[2], max_span_weights=(float('nan'),1,1,1,1)),
                   GenerationConfig(max_span_weights=(1,)*5)]
        for config in configs:
            with self.subTest(config=config), self.assertRaises(ValueError):
                generate(config, self.stats)

    def test_structure_actual_controls(self):
        config = GenerationConfig(count=30, mode=MODES[2], front_excluded=tuple(range(15,36)),
                                  start_span_weights=(0, 1, 0, 0, 0), max_span_weights=(1, 0, 0, 0, 0))
        tickets = generate(config, self.stats, rng=self.rng)
        self.assertTrue(all(features(t.front).start_span == 1 and features(t.front).max_span == 0 for t in tickets))
        impossible = replace(config, front_fixed=(1,))
        with self.assertRaisesRegex(ValueError, '没有可用'):
            generate(impossible, self.stats)

    def test_weight_probability_exact(self):
        weights = {1: 1, 2: 2, 3: 3}
        probs = [subset_probability(pair, (1,2,3), weights) for pair in combinations((1,2,3), 2)]
        self.assertAlmostEqual(sum(probs), 1)
        self.assertAlmostEqual(probs[0], 2/11)
        self.assertAlmostEqual(probs[1], 3/11)
        self.assertAlmostEqual(probs[2], 6/11)
        self.assertEqual(subset_probability(tuple(range(1,36)), tuple(range(1,36)), {i: 1 for i in range(1,36)}), 1)

    def test_weighted_sample_follows_actual_weights(self):
        weights = {1: 1, 2: 2, 3: 3}
        counts = Counter(tuple(weighted_sample((1,2,3), 2, weights, self.rng)) for _ in range(30000))
        for pair, expected in [((1,2), 2/11), ((1,3), 3/11), ((2,3), 6/11)]:
            self.assertAlmostEqual(counts[pair]/30000, expected, delta=0.012)

    def test_cancel(self):
        cancel = Event()
        cancel.set()
        with self.assertRaises(Cancelled):
            generate(GenerationConfig(), cancel=cancel)
        cancel.clear()
        with self.assertRaises(Cancelled):
            generate(GenerationConfig(mode=MODES[2]), self.stats, cancel, lambda _: cancel.set())

    def test_import_does_not_change_uniform_sequence(self):
        cfg = GenerationConfig(count=10)
        self.assertEqual(generate(cfg, self.stats, rng=random.Random(123)), generate(cfg, rng=random.Random(123)))

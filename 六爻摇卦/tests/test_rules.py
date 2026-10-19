"""穷举三枚铜钱，验证概率及阴阳变换，不依赖随机样本。"""
import itertools
import unittest
from collections import Counter

from liuyao_tool.domain.yao import Hexagram, YAO_TYPES, YANG_SYMBOL, YIN_SYMBOL
from liuyao_tool.generation.coins import toss_line


class CoinSequence:
    def __init__(self, values):
        self.values = iter(values)

    def choice(self, options):
        assert options == (2, 3)
        return next(self.values)


class RulesTests(unittest.TestCase):
    def test_all_eight_coin_combinations_have_the_expected_distribution(self):
        counts = Counter(
            toss_line(CoinSequence(values)).value
            for values in itertools.product((2, 3), repeat=3)
        )
        self.assertEqual(counts, {6: 1, 7: 3, 8: 3, 9: 1})

    def test_old_yin_and_yang_change_but_young_lines_do_not(self):
        for value, original, changed, moving in (
            (6, False, True, True),
            (7, True, True, False),
            (8, False, False, False),
            (9, True, False, True),
        ):
            with self.subTest(value=value):
                line = YAO_TYPES[value]
                self.assertEqual(line.is_yang, original)
                self.assertEqual(line.changed_is_yang, changed)
                self.assertEqual(line.is_changing, moving)

    def test_hexagram_keeps_bottom_to_top_order(self):
        result = Hexagram(tuple(YAO_TYPES[v] for v in (6, 7, 8, 9, 7, 8)))
        self.assertTrue(result.has_changes)
        self.assertEqual(result.changed_symbols, (
            YANG_SYMBOL, YANG_SYMBOL, YIN_SYMBOL, YIN_SYMBOL, YANG_SYMBOL, YIN_SYMBOL,
        ))

    def test_no_moving_lines_keeps_the_original_hexagram(self):
        result = Hexagram(tuple(YAO_TYPES[v] for v in (7, 8, 7, 8, 7, 8)))
        self.assertFalse(result.has_changes)
        self.assertEqual(result.changed_symbols, tuple(line.symbol for line in result.lines))

    def test_incomplete_hexagram_is_rejected(self):
        with self.assertRaises(ValueError):
            Hexagram((YAO_TYPES[7],) * 5)


if __name__ == "__main__":
    unittest.main()

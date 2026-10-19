"""用独立卦序矩阵校验全部卦画，避免上下卦或爻序颠倒。"""
import tempfile
import unittest

from liuyao_tool.domain.yao import Hexagram, YAO_TYPES
from liuyao_tool.storage.classics import get_catalog, load_catalog


class CatalogTests(unittest.TestCase):
    def test_all_64_entries_match_the_trigram_lookup_table(self):
        # 维基文库《周易》六十四卦速查表；行是下卦、列是上卦。
        patterns = ('111', '110', '101', '100', '011', '010', '001', '000')
        numbers = (
            (1, 43, 14, 34, 9, 5, 26, 11),
            (10, 58, 38, 54, 61, 60, 41, 19),
            (13, 49, 30, 55, 37, 63, 22, 36),
            (25, 17, 21, 51, 42, 3, 27, 24),
            (44, 28, 50, 32, 57, 48, 18, 46),
            (6, 47, 64, 40, 59, 29, 4, 7),
            (33, 31, 56, 62, 53, 39, 52, 15),
            (12, 45, 35, 16, 20, 8, 23, 2),
        )
        catalog = get_catalog()
        for lower, row in zip(patterns, numbers):
            for upper, number in zip(patterns, row):
                with self.subTest(number=number):
                    result = Hexagram(tuple(YAO_TYPES[7 if bit == '1' else 8] for bit in lower + upper))
                    self.assertEqual(catalog.identify(result).number, number)

    def test_every_entry_has_six_ordered_lines_and_a_fixed_source(self):
        catalog = get_catalog()
        self.assertEqual(len(catalog.entries), 64)
        for entry in catalog.entries:
            self.assertTrue(entry.judgement)
            self.assertTrue(entry.image)
            self.assertIn('oldid=', entry.source_revision_url)
            self.assertTrue(entry.source_url.startswith('https://zh.wikisource.org/'))
            for index, marker in enumerate(('初', '二', '三', '四', '五', '上')):
                self.assertIn(marker, entry.lines[index].label)
                self.assertTrue(entry.lines[index].text)

    def test_only_qian_and_kun_have_special_texts(self):
        special = {entry.number: entry.special[0].label for entry in get_catalog().entries if entry.special}
        self.assertEqual(special, {1: '用九', 2: '用六'})

    def test_missing_data_is_reported_instead_of_returning_partial_results(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, '六十四卦'):
                load_catalog(directory)


if __name__ == '__main__':
    unittest.main()

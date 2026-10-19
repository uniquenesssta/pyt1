"""覆盖全部 4096 种爻态组合及资料、推测分离的输出规则。"""
import itertools
import unittest

from liuyao_tool.domain.yao import Hexagram, YAO_TYPES
from liuyao_tool.interpretation.context import match_topics
from liuyao_tool.interpretation.engine import analyze
from liuyao_tool.interpretation.formatting import format_reading, format_references
from liuyao_tool.storage.classics import get_catalog


def make_hexagram(values):
    return Hexagram(tuple(YAO_TYPES[value] for value in values))


class ReadingTests(unittest.TestCase):
    def test_all_4096_combinations_resolve_and_render(self):
        catalog = get_catalog()
        seen = set()
        for values in itertools.product((6, 7, 8, 9), repeat=6):
            result = make_hexagram(values)
            report = analyze(result, catalog)
            self.assertEqual(len(report.moving), sum(v in (6, 9) for v in values))
            self.assertEqual(report.original.pattern, ''.join('1' if v in (7, 9) else '0' for v in values))
            self.assertEqual(report.changed.pattern, ''.join('1' if v in (6, 7) else '0' for v in values))
            self.assertIn('【原文依据】', format_reading(report))
            self.assertIn('【参考解读', format_reading(report))
            self.assertIn(report.original.judgement, format_references(report))
            seen.add((report.original.number, report.changed.number))
        self.assertEqual(len(seen), 4096)

    def test_bottom_moving_line_changes_qian_to_gou(self):
        report = analyze(make_hexagram((9, 7, 7, 7, 7, 7)), get_catalog(), '设计项目如何推进？', '方案还未确认')
        self.assertEqual((report.original.number, report.changed.number), (1, 44))
        self.assertEqual(report.moving[0].label, '初九')
        self.assertIn('潛龍', report.moving[0].text)
        text = format_reading(report)
        self.assertIn('设计项目如何推进', text)
        self.assertIn('方案还未确认', text)
        self.assertIn('推进角度', text)
        self.assertIn('谨慎角度', text)
        self.assertIn('条件变化角度', text)
        self.assertIn(report.original.source_revision_url, text)

    def test_special_text_requires_six_moving_lines(self):
        catalog = get_catalog()
        for values, label in (((9,) * 6, '用九'), ((6,) * 6, '用六')):
            report = analyze(make_hexagram(values), catalog)
            self.assertEqual(report.special[0].label, label)
            self.assertIn(label, format_reading(report))
        self.assertFalse(analyze(make_hexagram((9, 7, 7, 7, 7, 7)), catalog).special)

    def test_no_changes_keeps_one_reference_section(self):
        report = analyze(make_hexagram((7, 8, 7, 8, 7, 8)), get_catalog())
        self.assertEqual(report.original.number, report.changed.number)
        self.assertFalse(report.moving)
        self.assertIn('本轮没有动爻', format_reading(report))
        self.assertIn('之卦与本卦相同', format_references(report))

    def test_question_topics_take_priority_over_background(self):
        topics = match_topics('我想推进这个工作项目', '之前一直在处理感情问题')
        self.assertEqual([topic.name for topic in topics], ['工作与项目'])
        self.assertEqual(match_topics('', '正在练习新技能')[0].name, '学习与成长')
        self.assertEqual(match_topics('', '')[0].name, '综合阅读')


if __name__ == '__main__':
    unittest.main()

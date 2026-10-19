"""新一轮、问题修改和重新解读不能复制过期内容或重新起卦。"""
import unittest
from unittest.mock import Mock

from liuyao_tool.domain.yao import Hexagram, YAO_TYPES
from liuyao_tool.storage.classics import get_catalog
from liuyao_tool.ui.reading_controller import ReadingController


class ReadingControllerTests(unittest.TestCase):
    def setUp(self):
        self.root = Mock()
        self.panel = Mock()
        self.panel.get_context.return_value = ('项目怎样推进', '已有方案')
        self.controller = ReadingController(self.root, self.panel, get_catalog())
        self.result = Hexagram(tuple(YAO_TYPES[v] for v in (9, 7, 7, 7, 7, 7)))

    def test_context_change_blocks_copy_until_regeneration(self):
        self.controller.set_result(self.result)
        self.controller.context_changed()
        self.controller.copy()
        self.root.clipboard_append.assert_not_called()
        self.panel.show_stale.assert_called_once()
        self.panel.get_context.return_value = ('合作分工怎样沟通', '已经讨论过职责')
        self.controller.generate()
        self.controller.copy()
        copied = self.root.clipboard_append.call_args.args[0]
        self.assertIn('合作分工怎样沟通', copied)
        self.assertNotIn('项目怎样推进', copied)
        self.assertIn('乾为天', copied)
        self.assertIn('天风姤', copied)

    def test_new_round_clears_previous_result_without_erasing_inputs(self):
        self.controller.set_result(self.result)
        self.panel.reset_mock()
        self.controller.reset()
        self.controller.generate()
        self.controller.copy()
        self.panel.clear.assert_called_once()
        self.panel.get_context.assert_not_called()
        self.root.clipboard_append.assert_not_called()

    def test_regeneration_keeps_the_same_hexagram_and_changes_only_context(self):
        self.controller.set_result(self.result)
        first = self.panel.show_report.call_args.args[0].split('【问题与背景】')[0]
        self.panel.get_context.return_value = ('朋友之间如何沟通', '')
        self.controller.generate()
        second = self.panel.show_report.call_args.args[0]
        self.assertTrue(second.startswith(first))
        self.assertIn('关系与沟通', second)
        self.assertIn('未填写，不补造具体情节', second)


if __name__ == '__main__':
    unittest.main()

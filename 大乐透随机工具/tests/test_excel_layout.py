"""报表列识别与真实导入入口回归。"""
import tempfile
import unittest
from pathlib import Path
from test_excel import xlsx
from lottery.data.importing import load_dataset
from lottery.data.excel_layout import detect_columns


HEADER = ['开奖期号', '开奖日期', '前', '区', '', '', '', '后', '区', '投注总额']
ROW = ['07001', '2007-05-30', 22, 24, 29, 31, 35, 4, 11, 17086781]


class LayoutTests(unittest.TestCase):
    def test_shifted_header_and_horizontal_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'report.xlsx'
            xlsx(path, [[], ['']*10+HEADER, ROW+ROW, ['']*10+HEADER, ROW+ROW])
            result = load_dataset(path)
            self.assertEqual((len(result.draws),len(result.issues),result.ignored,result.duplicates),(2,0,3,1))
            self.assertEqual(result.draws[0].issue,'07001')
            self.assertEqual(result.draws[0].ticket.back,(4,11))

    def test_missing_selected_cell_is_not_replaced_by_prize(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'report.xlsx'
            broken=ROW.copy();broken[8]=None
            xlsx(path,[HEADER,ROW,broken,ROW[:8]])
            result=load_dataset(path)
            self.assertEqual((len(result.draws),len(result.issues)),(1,2))

    def test_unknown_header_not_guessed(self):
        self.assertIsNone(detect_columns(['开奖期号','日期']+['奖金']*7))

    def test_layout_does_not_leak_between_imports(self):
        # 模块不持有全局布局；连续导入普通表仍走完整行校验。
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'report.xlsx'
            xlsx(path,[HEADER,ROW]);load_dataset(path)
            xlsx(path,[[1,2,3,4,5,6,7]])
            self.assertEqual(load_dataset(path).draws[0].ticket.front,(1,2,3,4,5))

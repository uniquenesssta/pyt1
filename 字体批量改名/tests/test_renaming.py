import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fontTools.ttLib import TTFont, newTable
from font_renamer.config import STATUS_RENAME, STATUS_ERROR, STATUS_DONE
from font_renamer.core.models import RenamePlan
from font_renamer.core.naming import sanitize_filename, parse_int_list
from font_renamer.core.planning import build_rename_plan
from font_renamer.core.execution import execute_rename_plans
from font_renamer.storage.csv_log import write_csv_log


def font(path, name):
    f = TTFont()
    f['name'] = newTable('name')
    f['name'].names = []
    f['name'].setName(name, 4, 3, 1, 0x0804)
    f.save(path)
    f.close()


def plan(a, b):
    return RenamePlan(str(a), str(b), '', 4, 0x0804, STATUS_RENAME)


class RenamingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def scan(self, mode='自动添加数字后缀'):
        return build_rename_plan(str(self.root), ['.ttf'], [4], [0x0804], False, mode, True, True)

    def test_real_name_table_and_contents_unchanged(self):
        source = self.root / 'a.ttf'
        font(source, '中文 字体')
        before = source.read_bytes()
        plans = self.scan()
        self.assertTrue(source.exists())
        self.assertEqual(plans[0].new_name, '中文_字体.ttf')
        self.assertEqual(execute_rename_plans(plans), (1, 0))
        self.assertEqual((self.root / '中文_字体.ttf').read_bytes(), before)

    def test_directory_collision(self):
        font(self.root / 'a.ttf', '目标')
        (self.root / '目标.ttf').mkdir()
        self.assertEqual(self.scan()[0].new_name, '目标_1.ttf')
        self.assertEqual(self.scan('跳过重名文件')[0].status, '跳过')

    def test_duplicate_names(self):
        font(self.root / 'a.ttf', '字体')
        font(self.root / 'b.ttf', '字体')
        self.assertEqual([p.new_name for p in self.scan()], ['字体.ttf', '字体_1.ttf'])

    def test_swap(self):
        a, b = self.root / 'a.ttf', self.root / 'b.ttf'
        a.write_bytes(b'A'); b.write_bytes(b'B')
        self.assertEqual(execute_rename_plans([plan(a,b),plan(b,a)]), (2,0))
        self.assertEqual(a.read_bytes(), b'B')
        self.assertEqual(b.read_bytes(), b'A')

    def test_destination_appeared_after_preview(self):
        a,b = self.root / 'a.ttf', self.root / 'b.ttf'
        a.write_bytes(b'A'); b.write_bytes(b'B')
        p = plan(a,b)
        self.assertEqual(execute_rename_plans([p]), (0,1))
        self.assertEqual(a.read_bytes(), b'A')
        self.assertEqual(b.read_bytes(), b'B')
        self.assertFalse(list(self.root.glob('.__font*')))

    def test_case_only(self):
        a,b = self.root / 'A.ttf', self.root / 'a.ttf'
        a.write_bytes(b'A')
        self.assertEqual(execute_rename_plans([plan(a,b)]), (1,0))
        self.assertEqual(b.read_bytes(), b'A')

    def test_failed_rollback_reports_retained_file(self):
        a,b = self.root / 'a.ttf', self.root / 'b.ttf'
        a.write_bytes(b'A')
        import os
        rename = os.rename
        count = 0
        def fail_after_staging(src,dst):
            nonlocal count
            count += 1
            if count > 1: raise PermissionError('simulated lock')
            rename(src,dst)
        p = plan(a,b)
        with patch('font_renamer.core.execution.os.rename', side_effect=fail_after_staging):
            self.assertEqual(execute_rename_plans([p]), (0,1))
        retained = list(self.root.glob('.__font*'))
        self.assertEqual(len(retained), 1)
        self.assertIn(str(retained[0]), p.reason)
        self.assertEqual(retained[0].read_bytes(), b'A')

    def test_invalid_font_and_reserved_name(self):
        (self.root/'bad.ttf').write_bytes(b'bad')
        self.assertEqual(self.scan()[0].status, STATUS_ERROR)
        self.assertEqual(sanitize_filename('CON.foo'), '_CON.foo')
        with self.assertRaises(ValueError): parse_int_list('-1', [4])

    def test_log_unique_and_bom(self):
        p = plan(self.root/'a.ttf',self.root/'b.ttf')
        a = write_csv_log(str(self.root),[p])
        b = write_csv_log(str(self.root),[p])
        self.assertNotEqual(a,b)
        self.assertTrue(Path(a).read_bytes().startswith(b'\xef\xbb\xbf'))

if __name__ == '__main__':
    unittest.main()

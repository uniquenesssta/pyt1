"""真实 Tk 控件集成测试；无显示服务器时明确跳过，不用 mock 冒充运行。"""
from pathlib import Path
import tempfile
import time
import tkinter as tk
import unittest
from lottery.ui.app import LotteryApp


class UITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            root = tk.Tk()
            root.destroy()
        except tk.TclError as error:
            raise unittest.SkipTest(f'没有可用桌面，未执行真实 Tk 测试：{error}')

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = tk.Tk()
        self.app = LotteryApp(self.root, self.folder.name)
        self.errors = []
        self.app.error = lambda error, *args: self.errors.append(str(error))
        self.root.report_callback_exception = lambda kind, value, tb: self.errors.append(str(value))
        self.root.update()

    def tearDown(self):
        self.app.close()
        self.folder.cleanup()

    def finish(self):
        deadline = time.monotonic() + 20
        while self.app.jobs.running and time.monotonic() < deadline:
            self.root.update()
            time.sleep(.01)
        self.root.update()
        self.assertFalse(self.app.jobs.running, '后台任务超时')

    def test_generate_copy_favorite_persist_remove(self):
        self.app.controls.values['组数'].set('20')
        self.app.generate()
        self.finish()
        self.assertEqual(self.errors, [])
        self.assertEqual(len(self.app.generated.tickets), 20)
        table = self.app.generated.table
        table.tree.selection_set(('0', '1'))
        self.app.generated.copy()
        self.assertIn(' | ', self.root.clipboard_get())
        self.app.add_favorites(self.app.generated.selected())
        self.assertEqual(len(self.app.store.load()), 2)
        self.app.remove_favorites(self.app.favorites[:1])
        self.assertEqual(len(self.app.store.load()), 1)

    def test_import_search_statistics_generation_flow(self):
        path = Path(self.folder.name) / 'test.txt'
        path.write_text('2026001 1 2 3 22 35 1 12\n2026002 8 10 12 14 16 2 3\nbad\n', encoding='utf-8')
        self.app.load_path(path)
        self.finish()
        self.assertEqual(self.errors, [])
        self.assertEqual(self.app.stats.total, 2)
        self.assertEqual(len(self.app.dataset.issues), 1)
        self.assertTrue(self.app.statistics.rows)
        self.app.history.text.set('12')
        self.app.history.area.set('后区')
        self.app.search()
        self.finish()
        self.assertEqual(len(self.app.history.results), 1)
        self.app.controls.mode.set('历史频率加权')
        self.app.generate()
        self.finish()
        self.assertEqual(len(self.app.generated.tickets), 1)

    def test_failed_import_preserves_previous(self):
        valid = Path(self.folder.name) / 'valid.txt'
        valid.write_text('1 2 3 4 5 1 2')
        self.app.load_path(valid)
        self.finish()
        previous = self.app.dataset
        invalid = Path(self.folder.name) / 'bad.txt'
        invalid.write_text('invalid')
        self.app.load_path(invalid)
        self.finish()
        self.assertIs(self.app.dataset, previous)
        self.assertEqual(len(self.errors), 1)

    def test_pagination_and_sorted_selection(self):
        self.app.controls.values['组数'].set('600')
        self.app.generate()
        self.finish()
        table = self.app.generated.table
        self.assertEqual(len(table.rows), 600)
        self.assertEqual(len(table.tree.get_children()), 250)
        table.move(2)
        self.assertEqual(len(table.tree.get_children()), 100)
        table.sort(1)
        table.tree.selection_set('0')
        self.assertEqual(self.app.generated.selected()[0].text(), f'{table.rows[0][1]} | {table.rows[0][2]}')

    def test_cancel_preserves_previous(self):
        self.app.generate()
        self.finish()
        previous = self.app.generated.tickets
        self.app.controls.values['组数'].set('10000')
        self.app.generate()
        self.app.jobs.cancel.set()
        self.finish()
        self.assertIs(self.app.generated.tickets, previous)

"""真实 Tk 控件集成测试；无显示服务器时明确跳过，不用 mock 冒充运行。"""
from pathlib import Path
import tempfile
import time
import tkinter as tk
import unittest
from lottery.ui.app import LotteryApp
from lottery.core.models import Draw, Ticket
from lottery.core.generation import MODES


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

    def test_statistics_scope_follow_and_comparison_widgets(self):
        draws = [Draw(Ticket((1, 2, 3, 4, 5), (1, 2)), str(26001 + i)) for i in range(120)]
        page = self.app.statistics
        page.set_history(draws)
        self.assertEqual(page.hot_cold.report.total, 120)
        page.scope_buttons['近50期'].invoke()
        self.assertEqual((page.stats.total, page.hot_cold.report.total), (50, 50))
        page.hot_cold.period.set('近100期')
        page.hot_cold.period_box.event_generate('<<ComboboxSelected>>')
        self.root.update()
        page.scope_buttons['全部'].invoke()
        self.assertEqual((page.stats.total, page.hot_cold.report.total), (120, 100))
        page.hot_cold.period.set('跟随统计范围')
        page.hot_cold.period_box.event_generate('<<ComboboxSelected>>')
        self.root.update()
        self.assertEqual(page.hot_cold.report.total, 120)

    def test_constraints_stay_effective_when_collapsed_and_results_switch_back(self):
        controls = self.app.controls
        controls.constraints.button.invoke()
        controls.values['前区固定'].set('01 02')
        controls.constraints.button.invoke()
        self.assertFalse(controls.constraints.opened)
        self.assertIn('01 02', controls.constraint_summary.get())
        self.app.results_tabs.select(self.app.saved)
        self.app.generate()
        self.finish()
        self.assertEqual(self.app.results_tabs.select(), str(self.app.generated))
        self.assertTrue({1, 2}.issubset(self.app.generated.tickets[0].front))

    def test_structure_group_restore_pending_window_and_link(self):
        draws = [Draw(Ticket((1, 2, 8, 9, 15), (1, 2)), str(26001 + i)) for i in range(120)]
        page = self.app.structure_weights
        page.set_history(draws)
        original = page.profile
        page.period.set('100')
        page.period_box.event_generate('<<ComboboxSelected>>')
        self.root.update()
        self.assertIs(page.profile, original)
        with self.assertRaises(ValueError):
            page.snapshot()
        page.rebuild_button.invoke()
        page.family.set('跨区')
        page.family_box.event_generate('<<ComboboxSelected>>')
        self.root.update()
        self.assertEqual(page.group.get(), '最大跨区（差值>7）')
        self.app.controls.fill_button.invoke()
        self.assertEqual(self.app.controls.mode.get(), MODES[2])
        self.app.controls.weight_vars[0][0].set('75')
        page.restore_button.invoke()
        self.assertAlmostEqual(float(self.app.controls.weight_vars[0][0].get()), page.profile.weights[page.group.get()][0])

    def test_history_hidden_sources_remain_in_export_rows_and_reset(self):
        page = self.app.history
        draw = Draw(Ticket((1, 2, 3, 4, 5), (1, 2)), '26001', line=9, sheet='Sheet1')
        page.set_results([(draw, '匹配')], 1)
        self.assertEqual(len(page.table.tree['displaycolumns']), 4)
        self.assertEqual(len(page.table.rows[0]), 6)
        page.show_source.set(True)
        page.toggle_source()
        self.assertEqual(len(page.table.tree['displaycolumns']), 6)
        page.period.set('50')
        page.text.set('03')
        page.clear_filters()
        self.assertEqual((page.period.get(), page.text.get()), ('全部', ''))

    def assert_visible_inside(self, widget, container):
        self.assertTrue(widget.winfo_ismapped(), str(widget))
        self.assertGreater(widget.winfo_width(), 1)
        self.assertGreaterEqual(widget.winfo_rootx(), container.winfo_rootx())
        self.assertGreaterEqual(widget.winfo_rooty(), container.winfo_rooty())
        self.assertLessEqual(widget.winfo_rootx() + widget.winfo_width(), container.winfo_rootx() + container.winfo_width())
        self.assertLessEqual(widget.winfo_rooty() + widget.winfo_height(), container.winfo_rooty() + container.winfo_height())

    def test_small_window_keeps_bottom_actions_visible(self):
        self.root.geometry('1040x740')
        for page in (self.app.generation, self.app.history, self.app.statistics, self.app.structure_weights):
            self.app.tabs.select(page)
            self.root.update()
            self.assert_visible_inside(self.app.cancel_button, self.root)
        page = self.app.structure_weights
        for widget in (page.edit_entry, page.edit_button, page.restore_button):
            self.assert_visible_inside(widget, page)
        self.app.tabs.select(self.app.history)
        self.root.update()
        self.assert_visible_inside(self.app.history.copy_button, self.app.history)
        self.app.tabs.select(self.app.generation)
        self.root.update()
        self.assert_visible_inside(self.app.generated.summary, self.app.generated)
        self.assertEqual(self.errors, [])

    def test_statistics_tables_have_room_and_manual_split_is_preserved(self):
        page = self.app.statistics
        draws = [Draw(Ticket((1, 2, 3, 4, 5), (1, 2)), str(26001 + i)) for i in range(120)]
        page.set_history(draws)
        self.app.tabs.select(page)
        self.root.update()
        # Actual visible rows, rather than requested widget heights.
        for table in (page.table, *page.hot_cold.tables.values()):
            tree = table.tree
            visible = [tree.bbox(item) for item in tree.get_children()]
            complete = [box for box in visible if box and box[1] + box[3] <= tree.winfo_height()]
            self.assertGreaterEqual(len(complete), 4)
        position = round(page.panes.winfo_height() * .6)
        page.panes.sashpos(0, position)
        self.root.update()
        self.app.tabs.select(self.app.history)
        self.app.tabs.select(page)
        self.root.update()
        self.assertAlmostEqual(page.panes.sashpos(0), position, delta=3)
        self.assertEqual(self.errors, [])

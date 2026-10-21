"""验证筛选后的真实改名调用范围，使用临时文件。"""
import queue
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from font_renamer.config import STATUS_RENAME, STATUS_SKIP
from font_renamer.core.models import RenamePlan
from font_renamer.ui.app import FontRenamerApp
from font_renamer.ui.preview import PreviewMixin


class PreviewScopeTests(unittest.TestCase):
    def test_execute_filtered_results(self):
        for selected in ('全部', STATUS_RENAME, STATUS_SKIP):
            with self.subTest(selected=selected), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                source = root / 'a.ttf'
                source.write_bytes(b'font payload')
                skipped = root / 'skip.ttf'
                skipped.write_bytes(b'unchanged')
                plans = [
                    RenamePlan(str(source), str(root/'b.ttf'), '', 4, 0, STATUS_RENAME),
                    RenamePlan(str(skipped), str(root/'skip-new.ttf'), '', 4, 0, STATUS_SKIP),
                ]
                app = SimpleNamespace(busy=False, plans=plans, scan_folder=folder,
                    preview_filter_var=SimpleNamespace(get=lambda: selected),
                    work_queue=queue.Queue(), set_busy=Mock(), log=Mock())
                app._visible_plans = lambda: PreviewMixin._visible_plans(app)
                with patch('font_renamer.ui.app.messagebox.askyesno', return_value=True) as confirm, patch('font_renamer.ui.app.messagebox.showinfo'):
                    FontRenamerApp.rename_files(app)
                    if selected == STATUS_SKIP:
                        confirm.assert_not_called()
                        self.assertTrue(source.exists())
                    else:
                        app.worker.join(timeout=5)
                        self.assertFalse(app.worker.is_alive())
                        self.assertEqual((root/'b.ttf').read_bytes(), b'font payload')
                        self.assertIn('1 个', confirm.call_args.args[1])
                self.assertEqual(skipped.read_bytes(), b'unchanged')
                self.assertFalse((root/'skip-new.ttf').exists())
                self.assertEqual(len(app.plans), 2)

    def test_skip_filter_disables_execution(self):
        app = SimpleNamespace(plans=[SimpleNamespace(status=STATUS_RENAME)],
            preview_filter_var=SimpleNamespace(get=lambda: STATUS_SKIP),
            preview_filter=Mock(), scan_btn=Mock(), export_btn=Mock(), rename_btn=Mock(), progress=Mock())
        app._visible_plans = lambda: PreviewMixin._visible_plans(app)
        FontRenamerApp.set_busy(app, False)
        app.rename_btn.configure.assert_called_with(state='disabled')

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from font_renamer.core.models import RenamePlan
from font_renamer.core.preview_delete import delete_preview_files
from font_renamer.ui.preview_actions import PreviewActionsMixin


class BatchDeleteTests(unittest.TestCase):
    def test_selected_only_and_continue_after_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); trash=root/'trash';trash.mkdir()
            plans=[]
            for name in ('a.ttf','b.ttf','c.ttf','unselected.ttf'):
                p=root/name;p.write_bytes(name.encode())
                plans.append(RenamePlan(str(p),'','',None,None,'错误'))
            def recycle(path):
                if Path(path).name=='b.ttf':raise PermissionError('locked')
                Path(path).rename(trash/Path(path).name)
            success,failed=delete_preview_files(plans[:3],recycle)
            self.assertEqual([p.old_name for p,_ in success],['a.ttf','c.ttf'])
            self.assertEqual([p.old_name for p,_ in failed],['b.ttf'])
            self.assertTrue((root/'b.ttf').exists())
            self.assertTrue((root/'unselected.ttf').exists())

    def test_cancelled_confirmation_never_starts_worker(self):
        plan=RenamePlan('a.ttf','','',None,None,'错误')
        app=SimpleNamespace(_context_plan=plan,busy=False,tree=Mock(),_preview_rows={'a':plan},plans=[plan],set_busy=Mock())
        app.tree.selection.return_value=('a',)
        with patch('font_renamer.ui.preview_actions.confirm_delete',return_value=False):
            PreviewActionsMixin.delete_preview_row(app)
        app.set_busy.assert_not_called()
        self.assertFalse(hasattr(app,'worker'))

    def test_ctrl_a_uses_only_visible_rows(self):
        app=SimpleNamespace(busy=False,tree=Mock())
        app.tree.get_children.return_value=('visible1','visible2')
        self.assertEqual(PreviewActionsMixin.select_all_preview(app),'break')
        app.tree.selection_set.assert_called_once_with(('visible1','visible2'))

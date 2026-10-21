import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from font_renamer.core.models import RenamePlan
from font_renamer.core.preview_delete import delete_preview_file
from font_renamer.config import STATUS_ERROR, STATUS_DONE
from font_renamer.ui.preview import PreviewMixin
from font_renamer.core.scan_session import scan_session
from font_renamer.core.font_comparison import FontComparison


class PreviewDeleteTests(unittest.TestCase):
    def test_error_filter_and_successful_rename_path(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); old=root/'old.ttf'; new=root/'new.ttf'
            old.write_bytes(b'other file'); new.write_bytes(b'renamed font')
            done=RenamePlan(str(old),str(new),'',4,0,STATUS_DONE)
            error=RenamePlan(str(old),'','',None,None,STATUS_ERROR)
            app=SimpleNamespace(plans=[done,error],preview_filter_var=SimpleNamespace(get=lambda:STATUS_ERROR))
            self.assertEqual(PreviewMixin._visible_plans(app),[error])
            trash=root/'trash';trash.mkdir()
            result=delete_preview_file(done,lambda path:Path(path).rename(trash/Path(path).name))
            self.assertEqual(result,str(new))
            self.assertEqual(old.read_bytes(),b'other file')
            self.assertEqual((trash/'new.ttf').read_bytes(),b'renamed font')

    def test_failure_does_not_remove_source(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'bad.ttf';p.write_bytes(b'bad')
            plan=RenamePlan(str(p),'','',None,None,STATUS_ERROR)
            with self.assertRaises(PermissionError):
                delete_preview_file(plan,Mock(side_effect=PermissionError('locked')))
            self.assertTrue(p.exists())

    def test_missing_source_does_not_delete_target(self):
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/'target.ttf';target.write_bytes(b'keep')
            plan=RenamePlan(str(Path(folder)/'missing.ttf'),str(target),'',None,None,STATUS_ERROR)
            recycle=Mock()
            with self.assertRaises(ValueError):delete_preview_file(plan,recycle)
            recycle.assert_not_called()
            self.assertTrue(target.exists())

    def test_parse_error_with_readable_name_is_error_plan(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'bad.ttf';p.write_bytes(b'bad')
            info=FontComparison(str(p),'',3,error='invalid cmap',rename_name=SimpleNamespace(text='Readable'))
            config=dict(folder=folder,extensions=['.ttf'],name_ids=[4],lang_ids=[0x0804],recursive=False,duplicate_mode='自动添加数字后缀',lower_extension=True,use_underscore=True)
            with patch('font_renamer.core.scan_session.read_comparison',return_value=info):
                session=scan_session(config)
            self.assertEqual(session.plans[0].status,STATUS_ERROR)
            self.assertIn('invalid cmap',session.plans[0].reason)

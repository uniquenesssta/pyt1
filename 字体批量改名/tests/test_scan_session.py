import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from test_same_names import font
from font_renamer.core.scan_session import scan_session
from font_renamer.core import scan_session as module


class SharedScanTests(unittest.TestCase):
    def test_one_enumeration_one_parse_and_reused_results(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            font(root/'a.ttf','测试字体','Version 1')
            (root/'b.ttf').write_bytes((root/'a.ttf').read_bytes())
            font(root/'c.ttf','测试字体','Version 2')
            config=dict(folder=folder,extensions=['.ttf'],name_ids=[4],lang_ids=[0x0804],recursive=False,duplicate_mode='自动添加数字后缀',lower_extension=True,use_underscore=True)
            with patch.object(module,'iter_font_files',wraps=module.iter_font_files) as enumerate_files, patch.object(module,'read_comparison',wraps=module.read_comparison) as read, patch.object(module,'fingerprint',wraps=module.fingerprint) as hash_file:
                session=scan_session(config)
                self.assertEqual(enumerate_files.call_count,1)
                self.assertEqual(read.call_count,3)
                self.assertEqual(hash_file.call_count,3)
            from dataclasses import asdict
            def serial(items, reader, progress=None):
                results = []
                for item in items:
                    try: results.append((reader(item), None))
                    except Exception as exc: results.append((None, exc))
                return results
            with patch.object(module, 'parallel_read', side_effect=serial):
                sequential = scan_session(config)
            self.assertEqual(asdict(session), asdict(sequential))
            self.assertEqual(len(session.plans),3)
            self.assertEqual(len(session.duplicates),1)
            self.assertEqual(len(session.name_groups),1)
            self.assertEqual(session.errors,[])
            # 窗口复制缓存所需的数据不触发目录读取、元信息读取或内容哈希。
            import copy
            with patch('builtins.open',side_effect=AssertionError('unexpected file read')):
                self.assertEqual(len(copy.deepcopy(session.duplicates)),1)
                self.assertEqual(len(copy.deepcopy(session.name_groups)[0].members),3)

    def test_unique_size_unique_name_does_not_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            font(Path(folder)/'only.ttf','唯一字体','Version 1')
            config=dict(folder=folder,extensions=['.ttf'],name_ids=[4],lang_ids=[0x0804],recursive=False,duplicate_mode='自动添加数字后缀',lower_extension=True,use_underscore=True)
            with patch.object(module,'fingerprint',side_effect=AssertionError('unnecessary hash')):
                session=scan_session(config)
            self.assertEqual(len(session.plans),1)
            self.assertEqual(session.name_groups,[])
            self.assertEqual(session.duplicates,[])

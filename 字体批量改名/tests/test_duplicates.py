import tempfile
import unittest
from pathlib import Path
from font_renamer.core.duplicates import scan_duplicates, clean_duplicates


class DuplicateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'a.ttf').write_bytes(b'font-one')
        (self.root/'b.otf').write_bytes(b'font-one')
        (self.root/'c.ttf').write_bytes(b'font-two')

    def scan(self):
        return scan_duplicates(str(self.root), ['.ttf','.otf'], True)[0]

    def test_content_not_filename_and_scan_is_read_only(self):
        rows = self.scan()
        self.assertEqual(len(rows),1)
        self.assertEqual(Path(rows[0].keep).name,'a.ttf')
        self.assertEqual(Path(rows[0].path).name,'b.otf')
        self.assertTrue((self.root/'b.otf').exists())

    def test_changed_survivor_blocks_cleanup(self):
        rows = self.scan()
        (self.root/'a.ttf').write_bytes(b'changed!')
        called = []
        self.assertEqual(clean_duplicates(rows,called.append),0)
        self.assertFalse(called)
        self.assertEqual(rows[0].status,'失败')

    def test_missing_survivor_blocks_cleanup(self):
        rows = self.scan()
        (self.root/'a.ttf').unlink()
        self.assertEqual(clean_duplicates(rows,lambda _: self.fail('must not recycle')),0)

    def test_selected_only_and_retains_survivor(self):
        (self.root/'d.ttf').write_bytes(b'font-one')
        rows = self.scan()
        trash = self.root/'test-trash'; trash.mkdir()
        def recycle(path):
            Path(path).rename(trash/Path(path).name)
        self.assertEqual(clean_duplicates(rows[:1],recycle),1)
        self.assertTrue((self.root/'a.ttf').exists())
        self.assertTrue(Path(rows[1].path).exists())
        self.assertEqual((trash/'b.otf').read_bytes(),b'font-one')

    def test_recycle_failure_keeps_source(self):
        rows = self.scan()
        def fail(_): raise PermissionError('in use')
        self.assertEqual(clean_duplicates(rows,fail),0)
        self.assertTrue(Path(rows[0].path).exists())
        self.assertIn('in use',rows[0].reason)

    def test_changed_duplicate_blocks_cleanup(self):
        rows = self.scan()
        Path(rows[0].path).write_bytes(b'new-data')
        self.assertEqual(clean_duplicates(rows,lambda _: self.fail('must not recycle')),0)

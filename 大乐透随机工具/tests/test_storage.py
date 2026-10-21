from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from lottery.core.models import Ticket
from lottery.data.storage import FavoriteStore, atomic_write


class StorageTests(unittest.TestCase):
    def test_favorites_survive_restart(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / '收藏.json'
            ticket = Ticket((1,3,15,22,35), (1,12))
            self.assertEqual(FavoriteStore(path).load(), [])
            FavoriteStore(path).save([ticket])
            self.assertEqual(FavoriteStore(path).load(), [ticket])
            FavoriteStore(path).save([])
            self.assertEqual(FavoriteStore(path).load(), [])

    def test_corruption_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'favorites.json'
            path.write_text('{bad', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, '原文件未覆盖'):
                FavoriteStore(path).load()
            self.assertEqual(path.read_text(), '{bad')

    def test_write_failure_keeps_previous_and_cleans_temp(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'favorites.json'
            path.write_text('old')
            with patch('lottery.data.storage.os.replace', side_effect=PermissionError('locked')):
                with self.assertRaises(PermissionError):
                    atomic_write(path, 'new')
            self.assertEqual(path.read_text(), 'old')
            self.assertEqual(list(Path(folder).iterdir()), [path])

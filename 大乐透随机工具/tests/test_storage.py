from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from lottery.data.storage import atomic_write


class StorageTests(unittest.TestCase):
    def test_write_failure_keeps_previous_and_cleans_temp(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'favorites.json'
            path.write_text('old')
            with patch('lottery.data.storage.os.replace', side_effect=PermissionError('locked')):
                with self.assertRaises(PermissionError):
                    atomic_write(path, 'new')
            self.assertEqual(path.read_text(), 'old')
            self.assertEqual(list(Path(folder).iterdir()), [path])

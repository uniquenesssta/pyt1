"""Verify that pre-date favorites survive updates without invented timestamps."""
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from lottery.core.favorites import FavoriteRecord, new_favorites, newest_first
from lottery.core.models import Ticket
from lottery.data.favorite_store import FavoriteStore


class FavoriteStoreTests(unittest.TestCase):
    def test_legacy_file_and_new_dates_survive_restart(self):
        old = Ticket((1, 3, 15, 22, 35), (1, 12))
        first = Ticket((3, 5, 15, 22, 35), (6, 9))
        second = Ticket((1, 5, 15, 22, 30), (1, 12))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "收藏.json"
            self.assertEqual(FavoriteStore(path).load(), [])
            original = json.dumps({"version": 1, "tickets": [{"front": old.front, "back": old.back}]})
            path.write_text(original, encoding="utf-8")
            records = FavoriteStore(path).load()
            self.assertEqual(records, [FavoriteRecord(old)])
            self.assertEqual(path.read_text(encoding="utf-8"), original)

            records += new_favorites(records, [old, first, first], datetime(2026, 11, 18, 15, 40, tzinfo=timezone.utc))
            records += new_favorites(records, [first, second], datetime(2026, 11, 18, 16, 20, tzinfo=timezone.utc))
            FavoriteStore(path).save(records)
            restored = FavoriteStore(path).load()

            self.assertEqual([r.ticket for r in restored], [old, first, second])
            self.assertEqual([r.saved_at.isoformat() if r.saved_at else None for r in restored],
                             [None, "2026-11-18T23:40:00+08:00", "2026-11-19T00:20:00+08:00"])
            self.assertEqual([r.ticket for r in newest_first(restored)], [second, first, old])
            FavoriteStore(path).save([])
            self.assertEqual(FavoriteStore(path).load(), [])

    def test_bad_json_or_invalid_timestamp_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "favorites.json"
            without_timezone = ('{"version":1,"tickets":[{"front":[1,2,3,4,5],"back":[1,2],'
                                '"saved_at":"2026-11-18T08:03:00"}]}')
            for text in ("{bad", without_timezone):
                path.write_text(text, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "原文件未覆盖"):
                    FavoriteStore(path).load()
                self.assertEqual(path.read_text(encoding="utf-8"), text)

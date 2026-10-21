"""在线数据解析、更新保护与持久化，不依赖公网运行测试。"""
import tempfile
import unittest
from pathlib import Path
from threading import Event
from unittest.mock import patch
from lottery.data.online_feed import parse_feed, validate_update, download, MAX_BYTES
from lottery.data.history_store import HistoryStore
from lottery.core.models import Cancelled
from lottery.ui.history_actions import apply_history

ROW = b'07001 2007-05-30 22 24 29 31 35 04 11 9999999\n'
NEW = b'07002 2007-06-02 15 22 31 34 35 05 12 8888888\n'


class OnlineHistoryTests(unittest.TestCase):
    def test_parse_and_deduplicate(self):
        data = parse_feed(NEW + ROW + ROW)
        self.assertEqual([d.issue for d in data.draws], ['07001','07002'])
        self.assertEqual(data.duplicates, 1)
        self.assertEqual(data.draws[0].ticket.back, (4,11))

    def test_html_bad_date_bad_numbers_rejected(self):
        for raw in (b'<html>error</html>',ROW.replace(b'2007-05-30',b'2007-99-30'),ROW.replace(b'35 04',b'36 04'),b''):
            with self.assertRaises(ValueError):parse_feed(raw)

    def test_conflicting_duplicate_rejected(self):
        with self.assertRaises(ValueError):parse_feed(ROW+ROW.replace(b'35 04',b'34 04'))

    def test_update_count_missing_and_changed(self):
        previous=parse_feed(ROW)
        self.assertEqual(validate_update(parse_feed(ROW+NEW),previous),1)
        for incoming in (parse_feed(NEW),parse_feed(ROW.replace(b'35 04',b'34 04'))):
            with self.assertRaises(ValueError):validate_update(incoming,previous)

    def test_cancel(self):
        event=Event();event.set()
        with self.assertRaises(Cancelled):parse_feed(ROW,event)
        with self.assertRaises(Cancelled):download(event)

    def test_history_round_trip_and_failed_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=HistoryStore(Path(tmp)/'history.json')
            self.assertIsNone(store.load())
            store.save(parse_feed(ROW))
            with patch('lottery.data.storage.os.replace',side_effect=OSError('disk full')):
                with self.assertRaises(OSError):store.save(parse_feed(ROW+NEW))
            self.assertEqual(store.load().draws,parse_feed(ROW).draws)

    def test_invalid_cache_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=HistoryStore(Path(tmp)/'history.json');store.path.write_text('broken')
            with self.assertRaises(ValueError):store.load()
            self.assertEqual(store.path.read_text(),'broken')

    def test_download_reads_actual_response_interface(self):
        import io
        class Response(io.BytesIO):
            status=200
        with patch('lottery.data.online_feed.urlopen', return_value=Response(ROW)):
            self.assertEqual(download(),ROW)

    def test_failed_persistence_does_not_change_active_data(self):
        from types import SimpleNamespace
        errors=[]
        app=SimpleNamespace(dataset='original',stats='original stats',error=errors.append,
                            history_store=SimpleNamespace(save=lambda d: (_ for _ in ()).throw(OSError('disk full'))))
        apply_history(app,(parse_feed(ROW),'new stats'),'done')
        self.assertEqual(app.dataset,'original');self.assertEqual(len(errors),1)

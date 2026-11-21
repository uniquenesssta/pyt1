"""真实记录文件、开奖文本和对奖规则的一体化回归。"""
from dataclasses import replace
from datetime import date, datetime
from functools import partial
from pathlib import Path
import tempfile
import tkinter as tk
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from lottery.core.draw_calendar import expected_draw_date
from lottery.core.draw_index import DrawIndex
from lottery.core.favorites import FavoriteRecord
from lottery.core.models import Draw, Ticket
from lottery.core.pick_records import PickRecord, existing_pick
from lottery.core.prize_match import compare_pick
from lottery.data.favorite_store import FavoriteStore
from lottery.data.online_feed import parse_feed
from lottery.data.pick_store import PickStore
from lottery.ui.app import LotteryApp
from lottery.ui.favorite_panel import FavoritePanel
from lottery.ui.pick_log import ALL, LATEST, PickLogPanel


TICKET = Ticket((1, 2, 3, 4, 5), (1, 2))
MONDAY = b"26131 2026-11-16 06 07 08 09 10 03 04\n"
WEDNESDAY = b"26132 2026-11-18 01 02 03 04 05 01 02\n"
SATURDAY = b"26133 2026-11-21 02 03 04 05 06 01 03\n"


def timestamp(text):
    return datetime.fromisoformat(text + ":00+00:00")


class PickLogTests(unittest.TestCase):
    def test_cutoff_and_next_draw_use_beijing_time(self):
        cases = (
            ("2026-11-16T12:59", 16),
            ("2026-11-16T13:00", 18),
            ("2026-11-17T13:00", 18),
            ("2026-11-18T12:59", 18),
            ("2026-11-18T13:00", 21),
            ("2026-11-21T12:59", 21),
            ("2026-11-21T13:00", 23),
            ("2026-11-22T20:00", 23),
        )
        for time, day in cases:
            with self.subTest(time=time):
                self.assertEqual(expected_draw_date(timestamp(time)), date(2026, 11, day))

    def test_saved_record_uses_own_draw_after_updates_and_reopen(self):
        pick = PickRecord.from_selection(TICKET, timestamp("2026-11-18T12:59"))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "picks.json"
            PickStore(path).save([pick])
            saved, = PickStore(path).load()
        self.assertEqual(saved.saved_at.isoformat(), "2026-11-18T20:59:00+08:00")
        for source in (MONDAY, MONDAY + SATURDAY):
            draw, reason = DrawIndex(parse_feed(source).draws).resolve(saved)
            self.assertIsNone(draw)
            self.assertTrue(reason)
        index = DrawIndex(parse_feed(SATURDAY + MONDAY + WEDNESDAY).draws)
        draw, reason = index.resolve(saved)
        self.assertEqual((draw.issue, reason, index.latest.issue), ("26132", "", "26133"))
        match = compare_pick(saved.ticket, draw)
        self.assertEqual((match.front, match.back, match.prizes), (TICKET.front, TICKET.back, ((1, 1),)))

    def test_manual_issue_corrects_a_missing_day_or_missing_date(self):
        pick = PickRecord.from_selection(TICKET, timestamp("2026-11-18T12:59"))
        undated = Draw(TICKET, "26133")
        index = DrawIndex([undated])
        self.assertIsNone(index.resolve(pick)[0])
        self.assertEqual(index.resolve(replace(pick, issue="2026133")), (undated, ""))
        with self.assertRaises(ValueError):
            replace(pick, issue="未开奖")

    def test_conflicted_date_or_issue_never_produces_a_match(self):
        pick = PickRecord.from_selection(TICKET, timestamp("2026-11-18T12:59"))
        wed = parse_feed(WEDNESDAY).draws[0]
        wrong = replace(wed, ticket=Ticket((6, 7, 8, 9, 10), (1, 2)))
        self.assertIsNone(DrawIndex([wed, wrong]).resolve(pick)[0])
        self.assertIsNone(DrawIndex([wed, replace(wrong, issue="26133")]).resolve(pick)[0])
        self.assertEqual(DrawIndex([wed, replace(wed, issue="2026132")]).resolve(pick)[0], wed)

    def test_same_numbers_are_deduplicated_only_within_a_period(self):
        wed = PickRecord.from_selection(TICKET, timestamp("2026-11-18T12:59"))
        earlier = PickRecord.from_selection(TICKET, timestamp("2026-11-17T07:00"))
        sat = PickRecord.from_selection(TICKET, timestamp("2026-11-18T13:00"))
        index = DrawIndex()
        self.assertEqual(existing_pick([earlier], wed, index), earlier)
        self.assertIsNone(existing_pick([wed], sat, index))

    def test_compound_prize_counts_and_rule_change(self):
        compound = Ticket((1, 2, 3, 4, 5, 6), (1, 2, 3))
        new = compare_pick(compound, Draw(TICKET, "26014"))
        self.assertEqual(new.prizes, ((1, 1), (2, 2), (3, 5), (4, 10)))
        self.assertEqual(sum(count for _, count in new.prizes), compound.bets)
        old = compare_pick(compound, Draw(TICKET, "26013"))
        self.assertIsNone(old.prizes)
        miss = compare_pick(Ticket((6, 7, 8, 9, 10), (3, 4)), Draw(TICKET, "26014"))
        self.assertEqual(miss.prizes, ())

    def test_failed_storage_write_keeps_existing_records(self):
        pick = PickRecord.from_selection(TICKET, timestamp("2026-11-18T12:59"))
        with tempfile.TemporaryDirectory() as directory:
            store = PickStore(Path(directory) / "picks.json")
            store.save([pick])
            with patch("lottery.data.storage.os.replace", side_effect=OSError("disk full")):
                with self.assertRaises(OSError):
                    store.save([replace(pick, issue="26133")])
            self.assertEqual(store.load(), [pick])

    def test_record_from_favorites_is_visible_and_preserves_favorite_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = tk.Tcl()
            favorite_store = FavoriteStore(Path(directory) / "favorites.json")
            favorite_store.save([FavoriteRecord(TICKET, timestamp("2026-11-15T12:00"))])
            original = favorite_store.path.read_bytes()
            pick_store = PickStore(Path(directory) / "picks.json")
            table = Mock(rows=[], PAGE_SIZE=250)
            table.set_rows.side_effect = lambda rows: setattr(table, "rows", list(rows))
            status, error, tabs = Mock(), Mock(), Mock()
            panel = SimpleNamespace(table=table, history=DrawIndex(parse_feed(MONDAY).draws),
                                    scope=tk.StringVar(root, value=LATEST), scope_box=Mock(),
                                    load_error=None, store=pick_store, records=[], show_detail=Mock(), error=error)
            for name in ("record", "reveal_record", "save", "render"):
                setattr(panel, name, partial(getattr(PickLogPanel, name), panel))
            app = SimpleNamespace(pick_log=panel, results_tabs=tabs, set_status=status,
                                  favorites=favorite_store.load(),
                                  commit_favorites=lambda records: favorite_store.save(records))
            favorites = SimpleNamespace(selected=lambda: [TICKET], status=status,
                                        record=partial(LotteryApp.record_pick, app, show_log=True))

            with patch("lottery.ui.app.datetime") as clock:
                clock.now.return_value = timestamp("2026-11-18T12:59")
                FavoritePanel.record_selected(favorites)
                self.assertEqual(panel.scope.get(), ALL)
                self.assertEqual(table.rows[0][1:6],
                                 ("预计 2026-11-18", "01 02 03 04 05", "01 02", "—", "待开奖数据"))
                table.tree.selection_set.assert_called_once_with("0")
                tabs.select.assert_called_once_with(panel)
                FavoritePanel.record_selected(favorites)

            saved, = pick_store.load()
            self.assertEqual((saved.ticket, saved.target_date), (TICKET, date(2026, 11, 18)))
            self.assertEqual(favorite_store.path.read_bytes(), original)
            panel.history = DrawIndex(parse_feed(MONDAY + WEDNESDAY + SATURDAY).draws)
            panel.render()
            self.assertEqual(table.rows[0][1], "第 26132 期")
            self.assertEqual(table.rows[0][4], "5+2")
            error.assert_not_called()

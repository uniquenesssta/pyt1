from pathlib import Path
import tempfile
import unittest
from lottery.data.importing import load_dataset, parse_line, parse_text
from lottery.data.exporting import export_tickets, export_csv
from lottery.core.models import Ticket


class ImportTests(unittest.TestCase):
    def test_all_supported_formats(self):
        for line in ['1 3 15 22 35 1 12', '01,03,15,22,35|01,12',
                     '前区: 01 03 15 22 35 后区: 01 12', '1，3，15，22，35+1，12']:
            with self.subTest(line=line):
                self.assertEqual(parse_line(line).ticket, Ticket((1, 3, 15, 22, 35), (1, 12)))

    def test_issue_not_counted_as_number(self):
        draw = parse_line('2026123 35 22 15 03 01 12 01')
        self.assertEqual(draw.issue, '2026123')
        self.assertEqual(draw.ticket.front, (1, 3, 15, 22, 35))

    def test_invalid_rows_are_atomic(self):
        invalid = ['1 1 2 3 4 1 2', '1 2 3 4 5 1 1', '1 2 3 4 36 1 2',
                   '1 2 3 4 5 1 13', '1 2 3 4 5 -1 2', '1 2 3 4 5 1.5 2',
                   '1 2 3 4 5 1 2 extra', '2026-01-01 1 2 3 4 5 1 2']
        result = parse_text('\n'.join(invalid))
        self.assertEqual(len(result.issues), len(invalid))
        self.assertEqual(result.draws, [])
        self.assertEqual(result.issues[3].line, 4)

    def test_duplicate_reporting_does_not_drop_data(self):
        result = parse_text('# comment\n\n1 2 3 4 5 1 2\n1 2 3 4 5 1 2\n123 1 2 3 4 5 1 2')
        self.assertEqual((len(result.draws), result.duplicates, result.ignored), (3, 1, 2))

    def test_encodings(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / '历史.txt'
            for encoding in ['utf-8-sig', 'utf-16', 'gb18030']:
                path.write_bytes('前区: 01 02 03 04 05 后区: 01 02'.encode(encoding))
                result = load_dataset(path)
                self.assertEqual(len(result.draws), 1)
                self.assertEqual(result.encoding, encoding)

    def test_empty_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'empty.txt'
            path.write_text('# test')
            with self.assertRaisesRegex(ValueError, '没有有效'):
                load_dataset(path)

    def test_export_round_trip_and_bom(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'numbers.txt'
            ticket = Ticket((1, 3, 15, 22, 35), (1, 12))
            export_tickets(path, [ticket])
            self.assertEqual(load_dataset(path).draws[0].ticket, ticket)
            export_csv(path, ['test'], [['=1+1']])
            self.assertTrue(path.read_bytes().startswith(b'\xef\xbb\xbf'))
            self.assertIn("'=1+1", path.read_text(encoding='utf-8-sig'))

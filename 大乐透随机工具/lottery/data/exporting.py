"""可再次读取的选号文本以及 Excel 友好的 UTF-8 BOM CSV。"""
import csv
import io
from .storage import atomic_write
from ..core.models import format_numbers


def export_tickets(path, tickets):
    atomic_write(path, "\n".join(ticket.text() for ticket in tickets) + "\n")


def export_csv(path, headings, rows):
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(headings)
    for row in rows:
        # 无效原文可能以Excel公式开头，导出时按文本写入。
        writer.writerow(["'" + value if isinstance(value, str) and value.startswith(("=", "+", "-", "@", "\t", "\r")) else value for value in row])
    atomic_write(path, output.getvalue(), "utf-8-sig")


def draw_rows(results):
    return [(draw.issue, format_numbers(draw.ticket.front), format_numbers(draw.ticket.back), detail, draw.line, draw.sheet)
            for draw, detail in results]

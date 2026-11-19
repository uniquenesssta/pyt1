"""选号列表、复制、收藏和导出，不与其他表共享行 ID。"""
from tkinter import ttk, filedialog
from ..core.models import Ticket, format_numbers, parse_numbers
from ..data.exporting import export_tickets
from .table import DataTable
from .widgets import wrapped_label


class TicketPanel(ttk.Frame):
    def __init__(self, parent, title, status, error, action, action_text, on_open=None,
                 *, label_column="序号 / 规格", widths=(90, 630, 300)):
        super().__init__(parent, padding=10)
        self.status, self.error = status, error
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(0, 8))
        ttk.Button(toolbar, text="复制选中", command=self.copy).pack(side="left")
        ttk.Button(toolbar, text="导出全部", command=self.export).pack(side="left", padx=5)
        ttk.Button(toolbar, text=action_text, command=lambda: action(self.selected())).pack(side="right")
        if on_open is not None:
            ttk.Label(toolbar, text="双击一组号码，按期记录并收藏", style="Muted.TLabel").pack(side="left", padx=8)
        empty = '设置参数后点击“生成号码”' if title == '本批号码' else '选中本批号码后点击“收藏选中”，收藏会自动保存'
        self.table = DataTable(self, (label_column, "前区号码", "后区号码"), widths, empty_text=empty)
        self.table.pack(fill="both", expand=True)
        self.summary = wrapped_label(self, style="Muted.TLabel")
        self.summary.pack(side="bottom", before=self.table, fill="x", pady=(6, 0))
        self.table.tree.bind("<Control-c>", lambda _: self.copy())
        # Double-click affects the clicked row only, never unrelated multi-selection.
        open_ticket = on_open or (lambda ticket: action([ticket]))
        self.table.bind_open(lambda row: open_ticket(self.ticket_from_row(row)))
        self.set_tickets([])

    def set_tickets(self, tickets, *, label_sizes=False, labels=None):
        self.tickets = list(tickets)
        if labels is None:
            labels = (f"{len(t.front)}+{len(t.back)}" if label_sizes else i
                      for i, t in enumerate(self.tickets, 1))
        self.table.set_rows((label, format_numbers(t.front), format_numbers(t.back))
                            for label, t in zip(labels, self.tickets))
        if label_sizes:
            tiers = " · ".join(f"{len(t.front)}+{len(t.back)} {t.bets:,} 注" for t in self.tickets)
            self.summary.configure(text=f"同一套三档，逐档包含 · {tiers}（各档分别计算）")
        else:
            bets = sum(t.bets for t in self.tickets)
            self.summary.configure(text=f"{len(self.tickets):,} 组 · 普通复式 {bets:,} 注 · 基本金额 {bets*2:,} 元 · 含追加 {bets*3:,} 元（仅计算）")

    def selected(self):
        return [self.ticket_from_row(row) for row in self.table.selected()]

    @staticmethod
    def ticket_from_row(row):
        return Ticket(parse_numbers(row[1], 35), parse_numbers(row[2], 12))

    def copy(self):
        selected = self.selected()
        if not selected:
            self.status("请先选择号码，可按 Ctrl / Shift 多选，Ctrl+A 选择当前页")
            return
        try:
            self.clipboard_clear()
            self.clipboard_append("\n".join(t.text() for t in selected))
            self.status(f"已复制 {len(selected)} 组号码")
        except Exception as error:
            self.error(error)

    def export(self):
        if not self.tickets:
            self.status("暂无号码可导出")
            return
        path = filedialog.asksaveasfilename(parent=self, title="导出全部号码", defaultextension=".txt", filetypes=[("文本文件", "*.txt")])
        if path:
            try:
                export_tickets(path, self.tickets)
                self.status(f"已导出全部 {len(self.tickets):,} 组")
            except OSError as error:
                self.error(error)

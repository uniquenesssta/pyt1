"""统计分析页的前后区逐号遗漏明细。"""
import tkinter as tk
from tkinter import ttk

from ..core.omission import omission_report
from .table import DataTable
from .widgets import wrapped_label


class OmissionPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=6)
        row = ttk.Frame(self)
        row.pack(fill="x", pady=(0, 4))
        self.area = tk.StringVar(self, value="前区")
        self.summary = tk.StringVar(self, value="导入带期号的历史数据后可查看遗漏")
        for area in ("前区", "后区"):
            ttk.Radiobutton(row, text=area, variable=self.area, value=area,
                            command=self.render).pack(side="left", padx=(0, 6))
        wrapped_label(row, textvariable=self.summary, style="Muted.TLabel").pack(side="left", fill="x", expand=True)
        self.table = DataTable(self, ("号码", "当前遗漏", "最大已完成间隔", "平均已完成间隔", "窗口次数",
                                      "间隔样本数", "最后出现期号"), (65, 112, 140, 140, 100, 110, 140),
                               empty_text="暂无可核对的遗漏数据")
        self.table.tree.configure(height=5)
        self.table.pack(fill="both", expand=True)
        self.rows = ((), ())

    def set_history(self, draws, periods):
        if not draws:
            self.rows = ((), ())
            self.summary.set("导入带期号的历史数据后可查看遗漏")
        else:
            try:
                front, back, samples, streak, issue = omission_report(draws, periods)
            except ValueError as error:
                self.rows = ((), ())
                self.summary.set(str(error))
            else:
                self.rows = (front, back)
                self.summary.set(f"统计窗口 {samples:,} 期 · 截至 {issue} · 最新连续 {streak:,} 期；≥ 表示已知下限")
        self.render()

    def render(self):
        rows = self.rows[0 if self.area.get() == "前区" else 1]
        self.table.set_rows(
            (f"{row.number:02d}", f"≥{row.current}" if row.lower_bound else row.current,
             row.max_finished if row.max_finished is not None else "—",
             f"{row.average_finished:.2f}" if row.average_finished is not None else "—",
             row.occurrences, row.intervals, row.last_seen or "—")
            for row in rows
        )

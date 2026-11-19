"""条件频次报表：前区汇总、各参照号码明细和完整后区对子。"""
import tkinter as tk
from tkinter import ttk

from ..core.models import format_numbers
from .post_mode_controls import conditional_fields
from .table import DataTable
from .widgets import wrapped_label


FRONT_SUMMARY = "前区 Top 5 汇总"


class ConditionalFrequencyPanel(ttk.Frame):
    def __init__(self, parent, inputs, calculate):
        super().__init__(parent, padding=6)
        self.report = None
        self.details = {}
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x")
        conditional_fields(toolbar, inputs)
        self.calculate_button = ttk.Button(toolbar, text="计算", command=calculate)
        self.calculate_button.grid(row=0, column=2, sticky="sw", padx=(0, 8))
        self.view = tk.StringVar(self, value=FRONT_SUMMARY)
        self.view_box = ttk.Combobox(toolbar, textvariable=self.view, width=20, state="readonly")
        self.view_box.grid(row=0, column=3, sticky="sw")
        self.view_box.bind("<<ComboboxSelected>>", lambda _: self.render())
        self.summary = tk.StringVar(self)
        wrapped_label(self, textvariable=self.summary, style="Muted.TLabel").pack(fill="x", pady=(6, 4))
        self.table = DataTable(self, ("排名", "号码", "次数 / 票数", "占有效样本", "说明"),
                               (60, 60, 125, 125, 235), empty_text="选好参照期后点「计算」")
        self.table.tree.configure(height=5)
        self.table.pack(fill="both", expand=True)
        self.reset()

    def reset(self):
        self.report = None
        self.details.clear()
        self.view.set(FRONT_SUMMARY)
        self.view_box.configure(values=(FRONT_SUMMARY,), state="disabled")
        self.summary.set("独立于普通统计和冷热号；参照期之后的记录与缺失的相邻期不参与。")
        self.table.set_rows([])

    def set_busy(self, busy):
        self.calculate_button.configure(state="disabled" if busy else "normal")

    def set_report(self, report):
        self.report = report
        self.details = {f"前区 {row.condition[0]:02d} 开出后": row for row in report.front}
        self.details["后区整对 " + format_numbers(report.back.condition).replace(" ", "+")] = report.back
        options = (FRONT_SUMMARY, *self.details)
        self.view_box.configure(values=options, state="readonly")
        if self.view.get() not in options:
            self.view.set(FRONT_SUMMARY)
        self.render()

    def render(self):
        report = self.report
        if report is None:
            return
        window = f"参照 {report.anchor.issue} · {report.first_issue}–{report.anchor.issue} 共 {report.history_count:,} 期"
        view = self.view.get()
        if view == FRONT_SUMMARY:
            samples = "、".join(f"{row.condition[0]:02d}：{row.samples:,}" for row in report.front)
            self.summary.set(f"{window} · 前区有效样本 {samples}")
            votes = sorted(report.votes.items(), key=lambda item: (-item[1], item[0]))
            top_by_number = [(row.condition[0], row.top) for row in report.front]
            self.table.set_rows(
                (rank, f"{n:02d}", count, "—", "来自 " + format_numbers(
                    source for source, top in top_by_number if n in top))
                for rank, (n, count) in enumerate(votes, 1))
        else:
            row = self.details[view]
            self.summary.set(f"{window} · 出现 {row.occurrences:,} 次 / 有效下一期 {row.samples:,} 个 · 比例 = 次数 ÷ 有效样本")
            top = row.top
            self.table.set_rows(
                (rank, f"{n:02d}", row.counts[n], f"{row.counts[n] / row.samples:.2%}" if row.samples else "—",
                 "Top 5" if n in top else "")
                for rank, n in enumerate(row.ranking(), 1))

"""统计表、完整报表导出及可切换的频次图。"""
import tkinter as tk
from tkinter import ttk, filedialog
from ..core.statistics import report_rows
from ..core.statistics_window import window_statistics
from ..data.exporting import export_csv
from .table import DataTable
from .charts import BarChart
from .hot_cold import HotColdPanel
from .widgets import wrapped_label


class StatisticsPage(ttk.Frame):
    HEADINGS = ("类别", "项目", "次数", "统计基数", "百分比")

    def __init__(self, parent, status, error):
        super().__init__(parent, padding=16)
        self.status, self.error = status, error
        self.stats, self.rows = None, []
        self.draws = []
        self.active_periods = 0
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(0, 8))
        ttk.Label(toolbar, text="统计范围").pack(side="left")
        self.scope = tk.StringVar(value="全部")
        self.scope_buttons = {}
        for label in ("近50期", "近100期", "全部"):
            button = ttk.Button(toolbar, text=label, command=lambda value=label: self.choose_scope(value))
            button.pack(side="left", padx=(6, 0))
            self.scope_buttons[label] = button
        self.category = tk.StringVar(value="全部统计")
        self.categories = ttk.Combobox(toolbar, textvariable=self.category, values=("全部统计",), state="readonly", width=24)
        self.categories.pack(side="left", padx=16)
        self.categories.bind("<<ComboboxSelected>>", lambda _: self.filter())
        ttk.Button(toolbar, text="导出当前范围", command=self.export).pack(side="right")
        wrapped_label(self, text="双击次数回查开奖记录 · 百分比 = 次数 ÷ 统计基数；期数占比按记录数，号码频率按该区号码总数。", style="Muted.TLabel").pack(fill="x", pady=(0, 8))
        self.scope_summary = tk.StringVar(value="暂无历史数据 · 导入文件或在线更新后查看")
        wrapped_label(self, textvariable=self.scope_summary, style="Muted.TLabel").pack(fill="x", pady=(0, 12))
        panes = ttk.PanedWindow(self, orient="vertical")
        panes.pack(fill="both", expand=True)
        self.table = DataTable(panes, self.HEADINGS, (240, 180, 100, 100, 120))
        self.table.tree.configure(height=6)
        panes.add(self.table, weight=3)
        lower = self.lower_tabs = ttk.Notebook(panes)
        charts = ttk.Frame(lower, padding=12)
        row = ttk.Frame(charts)
        row.pack(fill="x", pady=6)
        self.chart_kind = tk.StringVar(value="前区次数")
        combo = ttk.Combobox(row, textvariable=self.chart_kind, values=("前区次数", "后区次数", "后区组合 TOP30"), state="readonly", width=20)
        combo.pack(side="left")
        combo.bind("<<ComboboxSelected>>", lambda _: self.draw_chart())
        self.chart = BarChart(charts)
        self.chart.pack(fill="both", expand=True)
        lower.add(charts, text="频次图表")
        self.hot_cold = HotColdPanel(lower)
        lower.insert(0, self.hot_cold, text="冷热号")
        lower.select(self.hot_cold)
        panes.add(lower, weight=2)
        self.update_scope_buttons()

    def choose_scope(self, value):
        self.scope.set(value)
        self.refresh_scope()

    def update_scope_buttons(self):
        for label, button in self.scope_buttons.items():
            button.configure(style="Primary.TButton" if label == self.scope.get() else "TButton")

    def set_history(self, draws):
        self.draws = list(draws)
        self.refresh_scope()

    def refresh_scope(self):
        periods = {"近50期": 50, "近100期": 100, "全部": 0}[self.scope.get()]
        self.update_scope_buttons()
        self.hot_cold.follow_scope(periods, self.draws)
        try:
            stats, caption = window_statistics(self.draws, periods)
        except ValueError as exc:
            self.stats, self.rows = None, []
            self.table.set_rows([])
            self.chart.set_values([], [])
            self.scope_summary.set(str(exc))
            self.error(exc)
            return
        self.active_periods = periods
        self.set_statistics(stats)
        self.scope_summary.set(f'{self.scope.get()} · {caption}')

    def set_busy(self, busy):
        for button in self.scope_buttons.values():
            button.configure(state="disabled" if busy else "normal")
        self.hot_cold.set_busy(busy)

    def set_statistics(self, stats):
        self.stats = stats
        self.rows = report_rows(stats)
        categories = ("全部统计",) + tuple(dict.fromkeys(r[0] for r in self.rows))
        self.categories.configure(values=categories)
        if self.category.get() not in categories:
            self.category.set("全部统计")
        self.filter()
        self.draw_chart()

    def filter(self):
        rows = [r for r in self.rows if self.category.get() == "全部统计" or r[0] == self.category.get()]
        self.table.set_rows(tuple(row[:4]) + (f"{row[4]:.4f}%",) for row in rows)

    def draw_chart(self):
        if self.stats is None:
            return
        kind = self.chart_kind.get()
        if kind == "后区组合 TOP30":
            pairs = sorted(self.stats.pairs.items(), key=lambda x: (-x[1], x[0]))[:30]
            self.chart.set_values(["-".join(f"{n:02d}" for n in pair) for pair, _ in pairs], [count for _, count in pairs])
        else:
            counter, maximum = (self.stats.front, 35) if kind == "前区次数" else (self.stats.back, 12)
            self.chart.set_values([f"{n:02d}" for n in range(1, maximum+1)], [counter[n] for n in range(1, maximum+1)])

    def export(self):
        if not self.rows:
            self.status("请先导入历史数据")
            return
        path = filedialog.asksaveasfilename(parent=self, defaultextension=".csv", filetypes=[("CSV 文件", "*.csv")], initialfile=f"统计_{self.scope.get()}.csv")
        if path:
            try:
                export_csv(path, self.HEADINGS, self.rows)
                self.status(f"已导出{self.scope.get()}范围内全部统计类别")
            except OSError as error:
                self.error(error)

"""统计表、完整报表导出及可切换的频次图。"""
import tkinter as tk
from tkinter import ttk, filedialog
from ..core.statistics import report_rows
from ..data.exporting import export_csv
from .table import DataTable
from .charts import BarChart


class StatisticsPage(ttk.Frame):
    HEADINGS = ("类别", "项目", "次数", "统计基数", "百分比")

    def __init__(self, parent, status, error):
        super().__init__(parent, padding=10)
        self.status, self.error = status, error
        self.stats, self.rows = None, []
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(0, 8))
        self.category = tk.StringVar(value="全部统计")
        self.categories = ttk.Combobox(toolbar, textvariable=self.category, values=("全部统计",), state="readonly", width=24)
        self.categories.pack(side="left")
        self.categories.bind("<<ComboboxSelected>>", lambda _: self.filter())
        ttk.Button(toolbar, text="导出全部统计", command=self.export).pack(side="right")
        ttk.Label(self, text="双击统计行查看对应开奖记录。期数占比 = 出现次数 ÷ 有效记录数；号码频率 = 出现次数 ÷ 该区号码总数。", style="Muted.TLabel").pack(anchor="w", pady=(0, 8))
        panes = ttk.PanedWindow(self, orient="vertical")
        panes.pack(fill="both", expand=True)
        self.table = DataTable(panes, self.HEADINGS, (240, 180, 100, 100, 120))
        panes.add(self.table, weight=3)
        charts = ttk.Frame(panes)
        row = ttk.Frame(charts)
        row.pack(fill="x", pady=6)
        self.chart_kind = tk.StringVar(value="前区次数")
        combo = ttk.Combobox(row, textvariable=self.chart_kind, values=("前区次数", "后区次数", "后区组合 TOP30"), state="readonly", width=20)
        combo.pack(side="left")
        combo.bind("<<ComboboxSelected>>", lambda _: self.draw_chart())
        self.chart = BarChart(charts)
        self.chart.pack(fill="both", expand=True)
        panes.add(charts, weight=2)

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
        path = filedialog.asksaveasfilename(parent=self, defaultextension=".csv", filetypes=[("CSV 文件", "*.csv")])
        if path:
            try:
                export_csv(path, self.HEADINGS, self.rows)
                self.status("已导出全部统计")
            except OSError as error:
                self.error(error)

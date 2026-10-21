"""共享导入结果的查询页。"""
import tkinter as tk
from tkinter import ttk, filedialog
from ..core.querying import Query
from ..data.exporting import export_csv, draw_rows
from .table import DataTable


class HistoryPage(ttk.Frame):
    HEADINGS = ("期号", "前区号码", "后区号码", "匹配位置", "原始行号", "工作表")

    def __init__(self, parent, search, status, error):
        super().__init__(parent, padding=10)
        self.status, self.error = status, error
        self.statistic = None
        self.search_command = search
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(0, 10))
        self.kind, self.area, self.mode = tk.StringVar(value="号码"), tk.StringVar(value="全部"), tk.StringVar(value="包含全部")
        kind = ttk.Combobox(toolbar, textvariable=self.kind, values=("号码", "期号"), width=7, state="readonly")
        kind.pack(side="left")
        self.area_box = ttk.Combobox(toolbar, textvariable=self.area, values=("全部", "前区", "后区"), width=7, state="readonly")
        self.area_box.pack(side="left", padx=5)
        self.mode_box = ttk.Combobox(toolbar, textvariable=self.mode, values=("包含全部", "包含任意", "连续位置"), width=10, state="readonly")
        self.mode_box.pack(side="left")
        self.text = tk.StringVar()
        entry = ttk.Entry(toolbar, textvariable=self.text, width=24)
        entry.pack(side="left", fill="x", expand=True, padx=8)
        entry.bind("<Return>", lambda _: search())
        self.search_button = ttk.Button(toolbar, text="查询", command=search)
        self.search_button.pack(side="left")
        ttk.Button(toolbar, text="导出全部匹配", command=self.export).pack(side="left", padx=(8, 0))
        ttk.Button(toolbar, text="复制选中", command=self.copy).pack(side="left", padx=(8, 0))
        kind.bind("<<ComboboxSelected>>", lambda _: self.update_kind())
        scope = ttk.Frame(self)
        scope.pack(fill="x", pady=(0, 6))
        ttk.Label(scope, text="最近期数").pack(side="left")
        self.period = tk.StringVar(value="全部")
        self.period_box = ttk.Combobox(scope, textvariable=self.period, values=("全部", "50", "100"), width=10)
        self.period_box.pack(side="left", padx=8)
        self.period_box.bind("<<ComboboxSelected>>", lambda _: search())
        self.period_box.bind("<Return>", lambda _: search())
        self.condition = tk.StringVar(value="未设置统计条件")
        ttk.Label(scope, textvariable=self.condition, wraplength=650).pack(side="left", padx=8)
        self.clear_button = ttk.Button(scope, text="清除统计条件", command=self.clear_statistic)
        self.clear_button.pack(side="right")
        ttk.Label(self, text="留空查看所选期数和统计条件内的记录；连续位置匹配不跨越前后区。号码按升序展示。", style="Muted.TLabel").pack(anchor="w", pady=(0, 8))
        self.table = DataTable(self, self.HEADINGS, (100, 230, 130, 280, 90, 120))
        self.table.pack(fill="both", expand=True)
        self.caption = ttk.Label(self)
        self.caption.pack(anchor="w", pady=(8, 0))
        self.results = []

    def periods(self):
        value = self.period.get().strip()
        if value == "全部": return 0
        try: result = int(value)
        except ValueError as exc: raise ValueError("期数请输入正整数，或选择全部") from exc
        if result <= 0: raise ValueError("期数须大于0")
        return result

    def clear_statistic(self):
        self.statistic = None
        self.condition.set("未设置统计条件")
        self.search_command()

    def reset_context(self):
        self.statistic = None
        self.condition.set("未设置统计条件")
        self.period.set("全部")

    def update_kind(self):
        modes = ("包含全部", "包含任意", "连续位置") if self.kind.get() == "号码" else ("完全一致", "前缀", "后三位")
        self.mode_box.configure(values=modes)
        self.mode.set(modes[0])
        self.area_box.configure(state="readonly" if self.kind.get() == "号码" else "disabled")

    def snapshot(self):
        return Query(self.text.get(), self.kind.get(), self.area.get(), self.mode.get())

    def set_results(self, results, total):
        self.results = results
        self.table.set_rows(draw_rows(results))
        self.caption.configure(text=f"共 {total:,} 条有效记录 · 匹配 {len(results):,} 条 · 占比 {len(results)/total*100 if total else 0:.2f}%")

    def export(self):
        if not self.results:
            self.status("暂无匹配结果")
            return
        path = filedialog.asksaveasfilename(parent=self, defaultextension=".csv", filetypes=[("CSV 文件", "*.csv")])
        if path:
            try:
                export_csv(path, self.HEADINGS, self.table.rows)
                self.status(f"已导出 {len(self.results):,} 条匹配记录")
            except OSError as error:
                self.error(error)

    def copy(self):
        rows = self.table.selected()
        if not rows:
            self.status("请先选择要复制的记录")
            return
        try:
            self.clipboard_clear()
            self.clipboard_append("\n".join("\t".join(map(str, row)) for row in rows))
            self.status(f"已复制 {len(rows)} 条记录")
        except tk.TclError as error:
            self.error(error)

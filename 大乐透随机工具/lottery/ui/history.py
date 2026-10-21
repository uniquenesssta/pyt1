"""历史查询：先选范围，再输入条件；统计回查条件单独展示。"""
import tkinter as tk
from tkinter import ttk, filedialog
from ..core.querying import Query
from ..data.exporting import export_csv, draw_rows
from .table import DataTable
from .widgets import field, wrapped_label


class HistoryPage(ttk.Frame):
    HEADINGS = ("期号", "前区号码", "后区号码", "匹配位置", "原始行号", "工作表")

    def __init__(self, parent, search, status, error):
        super().__init__(parent, padding=10)
        self.status, self.error = status, error
        self.statistic = None
        self.search_command = search
        self.on_return = lambda: None
        scope = ttk.Frame(self)
        scope.pack(fill="x", pady=(0, 8))
        ttk.Label(scope, text="最近期数").pack(side="left")
        self.period = tk.StringVar(value="全部")
        self.period_box = ttk.Combobox(scope, textvariable=self.period, values=("全部", "50", "100"), width=10)
        self.period_box.pack(side="left", padx=8)
        self.period_box.bind("<<ComboboxSelected>>", lambda _: search())
        self.period_box.bind("<Return>", lambda _: search())
        ttk.Label(scope, text="可输入自定义期数", style="Muted.TLabel").pack(side="left")
        ttk.Button(scope, text="导出匹配", command=self.export).pack(side="right")
        self.reset_button = ttk.Button(scope, text="清空筛选", command=self.clear_filters)
        self.reset_button.pack(side="right", padx=8)
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(0, 8))
        self.kind, self.area, self.mode = tk.StringVar(value="号码"), tk.StringVar(value="全部"), tk.StringVar(value="包含全部")
        kind = ttk.Combobox(field(toolbar, "查询类型", 0), textvariable=self.kind, values=("号码", "期号"), width=8, state="readonly")
        kind.pack(fill="x")
        self.area_box = ttk.Combobox(field(toolbar, "号码区域", 1), textvariable=self.area, values=("全部", "前区", "后区"), width=8, state="readonly")
        self.area_box.pack(fill="x")
        self.mode_box = ttk.Combobox(field(toolbar, "匹配方式", 2), textvariable=self.mode, values=("包含全部", "包含任意", "连续位置"), width=11, state="readonly")
        self.mode_box.pack(fill="x")
        self.text = tk.StringVar()
        entry = ttk.Entry(field(toolbar, "号码或期号（留空查全部）", 3, 1), textvariable=self.text, width=20)
        entry.pack(fill="x")
        entry.bind("<Return>", lambda _: search())
        self.search_button = ttk.Button(toolbar, text="查询", command=search, style="Primary.TButton")
        self.search_button.grid(row=0, column=4, sticky="s")
        kind.bind("<<ComboboxSelected>>", lambda _: self.update_kind())
        condition_row = ttk.Frame(self)
        condition_row.pack(fill="x", pady=(0, 8))
        self.condition = tk.StringVar(value="未设置统计条件")
        self.clear_button = ttk.Button(condition_row, text="清除统计条件", command=self.clear_statistic)
        self.clear_button.pack(side="right")
        self.back_button = ttk.Button(condition_row, text="返回统计来源", command=lambda: self.on_return())
        self.back_button.pack(side="right", padx=8)
        wrapped_label(condition_row, textvariable=self.condition, style="Muted.TLabel").pack(side="left", fill="x", expand=True)
        self.condition.trace_add("write", lambda *_: self.update_condition_buttons())
        self.table = DataTable(self, self.HEADINGS, (110, 300, 150, 350, 90, 120),
                               empty_text="暂无匹配结果；可清空筛选，或导入 / 更新历史数据")
        self.table.pack(fill="both", expand=True)
        bottom = ttk.Frame(self)
        bottom.pack(side="bottom", before=self.table, fill="x", pady=(6, 0))
        self.caption = wrapped_label(bottom, style="Muted.TLabel")
        self.caption.pack(side="left", fill="x", expand=True)
        self.show_source = tk.BooleanVar(value=False)
        ttk.Checkbutton(bottom, text="显示来源列", variable=self.show_source, command=self.toggle_source).pack(side="right", before=self.caption, padx=8)
        self.copy_button = ttk.Button(bottom, text="复制选中", command=self.copy)
        self.copy_button.pack(side="right", before=self.caption)
        self.table.tree.bind("<Control-c>", lambda _: self.copy())
        self.results = []
        self.toggle_source()
        self.update_condition_buttons()

    def toggle_source(self):
        self.table.tree.configure(displaycolumns=self.HEADINGS if self.show_source.get() else self.HEADINGS[:4])

    def update_condition_buttons(self):
        state = "normal" if self.statistic is not None else "disabled"
        self.clear_button.configure(state=state)
        self.back_button.configure(state=state)

    def clear_filters(self):
        self.reset_context()
        self.text.set("")
        self.kind.set("号码")
        self.area.set("全部")
        self.update_kind()
        self.search_command()

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

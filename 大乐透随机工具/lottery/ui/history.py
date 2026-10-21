"""共享导入结果的查询页。"""
import tkinter as tk
from tkinter import ttk, filedialog
from ..core.querying import Query
from ..data.exporting import export_csv, draw_rows
from .table import DataTable


class HistoryPage(ttk.Frame):
    HEADINGS = ("期号", "前区号码", "后区号码", "匹配位置", "原始行号")

    def __init__(self, parent, search, status, error):
        super().__init__(parent, padding=10)
        self.status, self.error = status, error
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
        ttk.Label(self, text="留空可查看全部记录；连续位置匹配不跨越前后区。号码按升序展示。", style="Muted.TLabel").pack(anchor="w", pady=(0, 8))
        self.table = DataTable(self, self.HEADINGS, (100, 230, 130, 340, 90))
        self.table.pack(fill="both", expand=True)
        self.caption = ttk.Label(self)
        self.caption.pack(anchor="w", pady=(8, 0))
        self.results = []

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

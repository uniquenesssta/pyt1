"""导入问题明细与完整导出。"""
import tkinter as tk
from tkinter import ttk, filedialog
from ..data.exporting import export_csv
from .table import DataTable


def show_import_issues(parent, dataset, error):
    window = tk.Toplevel(parent)
    window.title("导入校验明细")
    window.geometry("940x550")
    frame = ttk.Frame(window, padding=12)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text=f"无效 {len(dataset.issues):,} 行；空行/注释 {dataset.ignored:,} 行；重复记录 {dataset.duplicates:,} 行（保留并参与统计）。").pack(anchor="w", pady=(0, 8))
    table = DataTable(frame, ("行号", "原因", "原始内容"), (80, 300, 500))
    table.set_rows((i.line, i.reason, i.text) for i in dataset.issues)
    table.pack(fill="both", expand=True)

    def export():
        path = filedialog.asksaveasfilename(parent=window, defaultextension=".csv", filetypes=[("CSV 文件", "*.csv")])
        if path:
            try:
                export_csv(path, table.columns, table.rows)
            except OSError as exc:
                error(exc)
    ttk.Button(frame, text="导出全部无效行", command=export).pack(anchor="e", pady=(8, 0))

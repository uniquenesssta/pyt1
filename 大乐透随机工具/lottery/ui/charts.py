"""仅用 Tk Canvas 绘制真实统计数据，无 matplotlib/numpy 依赖。"""
import tkinter as tk
from tkinter import ttk


class BarChart(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, background="#ffffff", highlightthickness=0, height=240)
        scrollbar = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=scrollbar.set)
        self.canvas.pack(fill="both", expand=True)
        scrollbar.pack(fill="x")
        self.labels, self.values = [], []
        self.canvas.bind("<Configure>", lambda _: self.render())

    def set_values(self, labels, values):
        self.labels, self.values = list(labels), list(values)
        self.render()

    def render(self):
        canvas = self.canvas
        canvas.delete("all")
        if not self.values:
            canvas.create_text(30, 30, anchor="nw", text="导入历史数据后显示图表", fill="#64748b")
            return
        width = max(canvas.winfo_width(), len(self.values) * 48 + 70)
        height = max(160, canvas.winfo_height())
        canvas.configure(scrollregion=(0, 0, width, height))
        highest = max(self.values) or 1
        step = (width - 70) / len(self.values)
        bottom, top = height - 38, 34
        for i in range(5):
            value = highest * i / 4
            y = bottom - (bottom-top) * i / 4
            canvas.create_line(45, y, width - 10, y, fill="#e2e8f0")
            canvas.create_text(38, y, anchor="e", text=f"{value:.0f}", fill="#64748b")
        for i, (label, value) in enumerate(zip(self.labels, self.values)):
            x = 52 + i * step
            y = bottom - value / highest * (bottom-top)
            canvas.create_rectangle(x, y, x+step-12, bottom, fill="#3478c5", outline="")
            canvas.create_text(x+(step-12)/2, y-11, text=str(value), fill="#334155")
            canvas.create_text(x+(step-12)/2, bottom+17, text=label, fill="#475569")

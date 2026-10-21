"""统计下半区的近期前后区冷热号列表。"""
import tkinter as tk
from tkinter import ttk
from ..core.hot_cold import analyze_hot_cold
from .table import DataTable


class HotColdTable(DataTable):
    def render(self):
        super().render()
        for item in self.tree.get_children():
            self.tree.item(item, tags=(self.rows[int(item)][3],))


class HotColdPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=6)
        self.draws = []
        self.report = None
        self.on_open = lambda area, number, periods: None
        toolbar = ttk.Frame(self); toolbar.pack(fill='x')
        self.period = tk.IntVar(value=50)
        for n in (50,100):
            ttk.Radiobutton(toolbar,text=f'近{n}期',variable=self.period,value=n,command=self.refresh).pack(side='left',padx=5)
        self.summary = tk.StringVar(value='导入或更新历史后显示冷热号')
        ttk.Label(toolbar,textvariable=self.summary,wraplength=750).pack(side='left',padx=10)
        self.rule = tk.StringVar(value='按各区平均出现次数区分冷热；双击号码可回查。')
        ttk.Label(self,textvariable=self.rule,wraplength=1040).pack(fill='x',pady=4)
        columns = ttk.Frame(self); columns.pack(fill='both',expand=True)
        columns.columnconfigure(0,weight=1);columns.columnconfigure(1,weight=1);columns.rowconfigure(0,weight=1)
        self.tables = {}
        for col,area in enumerate(('前区','后区')):
            frame = ttk.LabelFrame(columns,text=area,padding=4)
            frame.grid(row=0,column=col,sticky='nsew',padx=3)
            table = HotColdTable(frame,('号码','次数','期数占比','冷热'),(70,75,100,70))
            table.tree.configure(height=5)
            table.tree.tag_configure('热号',foreground='#b42318')
            table.tree.tag_configure('冷号',foreground='#175cd3')
            # 排序和分页重绘时按冷热状态重新着色。
            table.pack(fill='both',expand=True)
            table.bind_open(lambda row,a=area:self.open_number(a,row))
            self.tables[area] = table

    def set_history(self, draws):
        self.draws = draws
        self.refresh()

    def refresh(self):
        self.report = None
        if not self.draws:
            self.summary.set('导入或更新历史后显示冷热号')
            for table in self.tables.values(): table.set_rows([])
            return
        try:
            r = analyze_hot_cold(self.draws,self.period.get())
        except ValueError as exc:
            self.summary.set(str(exc))
            for table in self.tables.values(): table.set_rows([])
            return
        self.report = r
        self.summary.set(f'实际{r.total}期 · {r.first}–{r.last} · {r.order}')
        self.rule.set(f'高于平均次数为热号，低于为冷号，相等为持平；前区均值 {r.total*5/35:.2f} 次，后区 {r.total*2/12:.2f} 次。双击回查；历史冷热不代表下期概率。')
        self.tables['前区'].set_rows(r.front)
        self.tables['后区'].set_rows(r.back)

    def open_number(self, area, row):
        if self.report:
            self.on_open(area,row[0],self.report.requested)

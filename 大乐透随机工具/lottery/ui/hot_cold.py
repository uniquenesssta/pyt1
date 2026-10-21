"""统计下半区的近期前后区冷热号列表。"""
import tkinter as tk
from tkinter import ttk
from ..core.hot_cold import analyze_hot_cold
from .table import DataTable
from .widgets import wrapped_label
from .theme import COLORS


class HotColdTable(DataTable):
    def render(self):
        super().render()
        for item in self.tree.get_children():
            self.tree.item(item, tags=('odd' if int(item) % 2 else 'even', self.rows[int(item)][3]))


class HotColdPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=12)
        self.draws = []
        self.report = None
        self.on_open = lambda area, number, periods: None
        toolbar = ttk.Frame(self); toolbar.pack(fill='x')
        self.main_periods = 0
        self.period = tk.StringVar(value='跟随统计范围')
        ttk.Label(toolbar, text='冷热号范围').pack(side='left')
        self.period_box = ttk.Combobox(toolbar, textvariable=self.period,
                                      values=('跟随统计范围', '近50期', '近100期'), state='readonly', width=16)
        self.period_box.pack(side='left', padx=8)
        self.period_box.bind('<<ComboboxSelected>>', lambda _: self.refresh())
        self.summary = tk.StringVar(value='导入或更新历史后显示冷热号')
        wrapped_label(toolbar, textvariable=self.summary, style='Muted.TLabel').pack(side='left',fill='x',expand=True,padx=10)
        self.rule = tk.StringVar(value='按各区平均出现次数区分冷热；双击号码可回查。')
        wrapped_label(self, textvariable=self.rule, style='Muted.TLabel').pack(fill='x',pady=(6, 8))
        columns = ttk.Frame(self); columns.pack(fill='both',expand=True)
        columns.columnconfigure(0,weight=1);columns.columnconfigure(1,weight=1);columns.rowconfigure(0,weight=1)
        self.tables = {}
        for col,area in enumerate(('前区','后区')):
            frame = ttk.LabelFrame(columns,text=area,padding=4)
            frame.grid(row=0,column=col,sticky='nsew',padx=3)
            table = HotColdTable(frame,('号码','次数','期数占比','冷热'),(70,75,100,70))
            table.tree.configure(height=5)
            table.tree.tag_configure('热号',foreground=COLORS['hot'])
            table.tree.tag_configure('冷号',foreground=COLORS['cold'])
            # 排序和分页重绘时按冷热状态重新着色。
            table.pack(fill='both',expand=True)
            table.bind_open(lambda row,a=area:self.open_number(a,row))
            self.tables[area] = table

    def set_history(self, draws):
        self.draws = list(draws)
        self.refresh()

    def follow_scope(self, periods, draws=None):
        self.main_periods = periods
        if draws is not None:
            self.draws = list(draws)
        self.refresh()

    def selected_periods(self):
        return self.main_periods if self.period.get() == '跟随统计范围' else {'近50期': 50, '近100期': 100}[self.period.get()]

    def set_busy(self, busy):
        self.period_box.configure(state='disabled' if busy else 'readonly')

    def refresh(self):
        self.report = None
        if not self.draws:
            self.summary.set('导入或更新历史后显示冷热号')
            for table in self.tables.values(): table.set_rows([])
            return
        try:
            r = analyze_hot_cold(self.draws,self.selected_periods())
        except ValueError as exc:
            self.summary.set(str(exc))
            for table in self.tables.values(): table.set_rows([])
            return
        self.report = r
        scope = f'近{r.requested}期' if r.requested else '全部'
        state = '跟随主范围' if self.period.get() == '跟随统计范围' else '独立对比'
        self.summary.set(f'{state} · {scope} · 实际 {r.total:,} 条 · {r.first}–{r.last}')
        self.rule.set(f'前区均值 {r.total*5/35:.2f} 次 / 后区 {r.total*2/12:.2f} 次；高于为热号，低于为冷号，相等为持平。双击回查；历史冷热不代表下期概率。')
        self.tables['前区'].set_rows(r.front)
        self.tables['后区'].set_rows(r.back)

    def open_number(self, area, row):
        if self.report:
            self.on_open(area,row[0],self.report.requested)

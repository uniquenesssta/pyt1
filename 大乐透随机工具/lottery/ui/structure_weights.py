"""历史窗口、细分结构分布与权重编辑面板。"""
from copy import deepcopy
import tkinter as tk
from tkinter import ttk
from ..core.structure_profile import build_profile, domains
from .table import DataTable


class StructureWeightsPage(ttk.Frame):
    def __init__(self, parent, error):
        super().__init__(parent, padding=10)
        self.error, self.draws, self.profile = error, [], None
        self.on_change = lambda profile: None
        top = ttk.Frame(self); top.pack(fill='x')
        ttk.Label(top, text='统计最近期数').pack(side='left')
        self.period = tk.StringVar(value='50')
        self.period_box = ttk.Combobox(top, textvariable=self.period, values=('50','100','全部'), width=10)
        self.period_box.pack(side='left', padx=8)
        self.rebuild_button = ttk.Button(top, text='统计并自动填入权重', command=self.rebuild)
        self.rebuild_button.pack(side='left')
        self.period_box.bind('<<ComboboxSelected>>', lambda _: self.rebuild())
        self.period_box.bind('<Return>', lambda _: self.rebuild())
        self.summary = tk.StringVar(value='请先导入或更新历史数据')
        ttk.Label(self, textvariable=self.summary, wraplength=1040).pack(fill='x', pady=8)
        row = ttk.Frame(self); row.pack(fill='x')
        self.group = tk.StringVar(value='C1差值')
        self.group_box = ttk.Combobox(row, textvariable=self.group, values=tuple(domains()), state='readonly', width=30)
        self.group_box.pack(side='left')
        self.group_box.bind('<<ComboboxSelected>>', lambda _: self.render())
        ttk.Label(row, text='本指标强度（0=关闭）').pack(side='left', padx=8)
        self.strength = tk.StringVar(value='1')
        ttk.Entry(row, textvariable=self.strength, width=6).pack(side='left')
        self.strength_button = ttk.Button(row, text='应用强度', command=self.apply_strength)
        self.strength_button.pack(side='left', padx=8)
        self.mean = tk.StringVar()
        ttk.Label(self, textvariable=self.mean, wraplength=1040).pack(fill='x', pady=8)
        self.table = DataTable(self, ('类别','历史次数','实际期数','历史占比','建议权重','当前权重'), (180,120,120,140,140,140))
        self.table.pack(fill='both', expand=True)
        row = ttk.Frame(self); row.pack(fill='x', pady=8)
        ttk.Label(row, text='选中类别的权重（0=排除）').pack(side='left')
        self.edit = tk.StringVar(value='1')
        ttk.Entry(row, textvariable=self.edit, width=10).pack(side='left', padx=8)
        self.edit_button = ttk.Button(row, text='应用到选中类别', command=self.apply_weight)
        self.edit_button.pack(side='left')
        ttk.Label(self, text='历史占比保留原始数据；建议权重加1平滑后自动填入，避免50期中未出现的类别被直接排除。\n均值仅供参考；实际生成使用完整分布与指标强度。权重是相对偏好，不是最终生成比例或中奖概率。', wraplength=1040).pack(fill='x')

    def periods(self):
        value = self.period.get().strip()
        if value == '全部': return 0
        try: number = int(value)
        except ValueError as exc: raise ValueError('请输入正整数期数，或选择全部') from exc
        if number <= 0: raise ValueError('自定义期数须大于0')
        return number

    def set_history(self, draws):
        self.draws = draws
        self.profile = None
        self.rebuild()

    def rebuild(self):
        try:
            profile = build_profile(self.draws, self.periods())
        except ValueError as exc:
            self.error(exc); return
        self.profile = profile
        self.describe()
        self.render()
        self.on_change(profile)

    def describe(self):
        profile = self.profile
        first, last = profile.draws[0], profile.draws[-1]
        self.summary.set(f'请求 {profile.requested or "全部"} 期 · 实际 {len(profile.draws)} 期 · {first.issue or first.line} → {last.issue or last.line} · {profile.order}；重新统计会恢复建议权重')

    def render(self):
        if not self.profile: return
        p, name = self.profile, self.group.get()
        self.strength.set(str(p.strengths[name]))
        average = p.means.get(name)
        if name.endswith('空区') or '中间覆盖' in name:
            description = '0=未发生，1=发生；均值即发生比例'
        elif name == '连号形态':
            description = '连续段长度组合：2+2+1 表示两组二连号加一个单号；1+1+1+1+1 表示无连号'
        else:
            description = 'C1–C4为排序后相邻号码差；最大跨区保留差值>7定义，起始跨区为最小号码分区减1'
        self.mean.set((f'历史均值：{average:.4f}；' if average is not None else '') + description)
        total = len(p.draws); keys = domains()[name]
        self.table.set_rows((str(k),p.counts[name][k],total,f'{100*p.counts[name][k]/total:.4f}%',f'{100*(p.counts[name][k]+1)/(total+len(keys)):.4f}',f'{p.weights[name][k]:.4f}') for k in keys)

    def apply_strength(self):
        if not self.profile: return
        try:
            new = deepcopy(self.profile)
            new.strengths[self.group.get()] = float(self.strength.get())
            new.validate()
            self.profile = new; self.render(); self.on_change(new)
        except ValueError as exc: self.error(exc)

    def apply_weight(self):
        if not self.profile: return
        try:
            selected = self.table.selected()
            if not selected: raise ValueError('请先选择要调整的类别')
            new = deepcopy(self.profile); name = self.group.get()
            keys = {str(k): k for k in domains()[name]}
            for row in selected: new.weights[name][keys[row[0]]] = float(self.edit.get())
            new.validate()
            self.profile = new; self.render(); self.on_change(new)
        except ValueError as exc: self.error(exc)

    def snapshot(self):
        if self.profile is None: raise ValueError('请在结构权重页先统计历史')
        if self.periods() != self.profile.requested:
            raise ValueError('期数已修改，请先点击“统计并自动填入权重”')
        self.profile.validate()
        return deepcopy(self.profile)

    def set_busy(self, busy):
        for widget in (self.rebuild_button,self.strength_button,self.edit_button,self.period_box):
            widget.configure(state='disabled' if busy else 'normal')

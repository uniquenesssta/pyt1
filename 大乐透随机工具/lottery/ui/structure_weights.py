"""历史结构的分组浏览、建议权重与手动调整。"""
from copy import deepcopy
import tkinter as tk
from tkinter import ttk
from ..core.structure_profile import build_profile, domains
from .table import DataTable
from .widgets import field, wrapped_label, Disclosure


GROUPS = {
    '差值': tuple(f'C{i}差值' for i in range(1, 5)),
    '连号': ('连号形态', '最长连号'),
    '空区': ('空区数量',) + tuple(f'{z}区空区' for z in range(1, 6)),
    '跨区': ('最大跨区（差值>7）', '起始跨区'),
    '中间覆盖': tuple(f'{z}区中间覆盖（差值>10）' for z in range(1, 6)),
}


class StructureWeightsPage(ttk.Frame):
    def __init__(self, parent, error):
        super().__init__(parent, padding=10)
        self.error, self.draws, self.profile = error, [], None
        self.on_change = lambda profile: None
        self.on_generate = lambda: None
        top = ttk.Frame(self)
        top.pack(fill='x')
        ttk.Label(top, text='最近期数').pack(side='left')
        self.period = tk.StringVar(value='50')
        self.period_box = ttk.Combobox(top, textvariable=self.period, values=('50','100','全部'), width=10)
        self.period_box.pack(side='left', padx=8)
        self.rebuild_button = ttk.Button(top, text='统计并自动填入权重', command=self.rebuild, style='Primary.TButton')
        self.rebuild_button.pack(side='left')
        ttk.Button(top, text='去随机选号', command=lambda: self.on_generate()).pack(side='right')
        self.period_box.bind('<Return>', lambda _: self.rebuild())
        self.pending = tk.StringVar(value='可输入自定义期数；重算会重置所有手动权重')
        wrapped_label(self, textvariable=self.pending, style='Muted.TLabel').pack(fill='x', pady=(4, 0))
        self.period.trace_add('write', lambda *_: self.describe_pending())
        self.summary = tk.StringVar(value='请先导入或更新历史数据')
        wrapped_label(self, textvariable=self.summary, style='Muted.TLabel').pack(fill='x', pady=(4, 8))
        row = ttk.Frame(self)
        row.pack(fill='x')
        self.family = tk.StringVar(value='差值')
        self.family_box = ttk.Combobox(field(row, '指标组', 0), textvariable=self.family, values=tuple(GROUPS), state='readonly', width=10)
        self.family_box.pack(fill='x')
        self.family_box.bind('<<ComboboxSelected>>', lambda _: self.select_family())
        self.group = tk.StringVar(value='C1差值')
        self.group_box = ttk.Combobox(field(row, '细分指标', 1), textvariable=self.group, values=GROUPS['差值'], state='readonly', width=22)
        self.group_box.pack(fill='x')
        self.group_box.bind('<<ComboboxSelected>>', lambda _: self.render())
        self.strength = tk.StringVar(value='1')
        self.strength_entry = ttk.Entry(field(row, '本指标强度（0=关闭）', 2), textvariable=self.strength, width=8)
        self.strength_entry.pack(fill='x')
        self.strength_entry.bind('<Return>', lambda _: self.apply_strength())
        self.strength_button = ttk.Button(row, text='应用强度', command=self.apply_strength)
        row.columnconfigure(3, weight=1)
        self.strength_button.grid(row=0, column=3, sticky='sw')
        self.mean = tk.StringVar(value='选择指标查看历史分布；双击次数回查开奖记录')
        wrapped_label(self, textvariable=self.mean, style='Muted.TLabel').pack(fill='x', pady=6)
        self.table = DataTable(self, ('类别','历史次数','实际期数','历史占比','建议权重','当前权重'), (150,120,120,140,140,140))
        self.table.pack(fill='both', expand=True)
        row = ttk.Frame(self)
        row.pack(side='bottom', before=self.table, fill='x', pady=6)
        ttk.Label(row, text='选中类别的权重（0=排除）').pack(side='left')
        self.edit = tk.StringVar(value='1')
        self.edit_entry = ttk.Entry(row, textvariable=self.edit, width=9)
        self.edit_entry.pack(side='left', padx=8)
        self.edit_entry.bind('<Return>', lambda _: self.apply_weight())
        self.edit_button = ttk.Button(row, text='应用到选中类别', command=self.apply_weight, style='Primary.TButton')
        self.edit_button.pack(side='left')
        self.restore_button = ttk.Button(row, text='恢复本指标建议权重', command=self.restore_group)
        self.restore_button.pack(side='right')
        self.table.tree.bind('<<TreeviewSelect>>', lambda _: self.describe_selection(), add='+')
        help_box = Disclosure(self, '权重说明')
        help_box.pack(side='bottom', before=row, fill='x')
        wrapped_label(help_box.body, text='历史次数与占比保留实际数据；建议权重加1平滑，避免近期未出现的类别被直接排除。均值只供参考，生成使用完整分布与指标强度。最长连号与连号形态、空区数量与各区空区有重叠，所以最长连号和空区数量的强度默认关闭。权重是相对偏好，不是最终生成比例或中奖概率。', style='Muted.TLabel').pack(fill='x')

    def select_family(self):
        names = GROUPS[self.family.get()]
        self.group_box.configure(values=names)
        self.group.set(names[0])
        self.render()

    def describe_pending(self):
        try:
            pending = self.profile is not None and self.periods() != self.profile.requested
        except ValueError:
            pending = True
        self.pending.set('期数尚未应用；点击统计后将重置所有手动权重' if pending else '可输入自定义期数；重算会重置所有手动权重')

    def describe_selection(self):
        selected = self.table.selected()
        if len(selected) == 1:
            self.edit.set(selected[0][-1])

    def restore_group(self):
        if not self.profile:
            return
        new = deepcopy(self.profile)
        name = self.group.get()
        keys = domains()[name]
        total = len(new.draws)
        new.weights[name] = {key: 100 * (new.counts[name][key] + 1) / (total + len(keys)) for key in keys}
        new.validate()
        self.profile = new
        self.render()
        self.on_change(new)

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
        self.summary.set(f'已应用：{profile.requested or "全部"} 期 · 实际 {len(profile.draws)} 期 · {first.issue or first.line} → {last.issue or last.line} · {profile.order}')
        self.describe_pending()

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
        for widget in (self.rebuild_button,self.strength_button,self.edit_button,self.period_box,self.restore_button,self.strength_entry,self.edit_entry):
            widget.configure(state='disabled' if busy else 'normal')
        for widget in (self.family_box, self.group_box):
            widget.configure(state='disabled' if busy else 'readonly')

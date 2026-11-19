"""历史结构的分组浏览、建议权重与手动调整。"""
from copy import deepcopy
import tkinter as tk
from tkinter import ttk
from ..core.structure_profile import INDICATORS, build_profile, domains
from ..core.temporal_indicators import TEMPORAL_INDICATORS
from .indicator_groups import GROUPS
from .structure_draw import StructureDrawPanel
from .table import DataTable
from .widgets import field, wrapped_label, Disclosure


WEIGHT_COLUMNS = ('类别', '历史次数', '有效样本', '历史占比', '理论占比', '建议权重', '当前权重')
CLASSIC_COLUMNS = tuple(name for name in WEIGHT_COLUMNS if name != '理论占比')


class StructureWeightsPage(ttk.Frame):
    def __init__(self, parent, error, inputs, draw, use_in_selection, indicator_selection):
        super().__init__(parent, padding=10)
        self.error, self.draws, self.profile = error, [], None
        self.indicator_selection = indicator_selection
        self.on_change = lambda profile: None
        self._busy = False
        top = ttk.Frame(self)
        top.pack(fill='x')
        ttk.Label(top, text='最近期数').pack(side='left')
        self.period = tk.StringVar(value='50')
        self.period_box = ttk.Combobox(top, textvariable=self.period, values=('50','100','全部'), width=10)
        self.period_box.pack(side='left', padx=8)
        self.rebuild_button = ttk.Button(top, text='统计并自动填入权重', command=self.rebuild, style='Primary.TButton')
        self.rebuild_button.pack(side='left')
        self.use_button = ttk.Button(top, text='应用到选号页', command=use_in_selection, state='disabled')
        self.use_button.pack(side='right')
        self.period_box.bind('<Return>', lambda _: self.rebuild())
        self.pending = tk.StringVar(value='可输入自定义期数；重算会重置所有手动权重')
        wrapped_label(self, textvariable=self.pending, style='Muted.TLabel').pack(fill='x', pady=(4, 0))
        self.summary = tk.StringVar(value='请先导入或更新历史数据')
        wrapped_label(self, textvariable=self.summary, style='Muted.TLabel').pack(fill='x', pady=(4, 8))
        wrapped_label(self, textvariable=indicator_selection.summary, style='Muted.TLabel').pack(fill='x', pady=(0, 6))
        row = ttk.Frame(self)
        row.pack(fill='x')
        self.family = tk.StringVar(value='差值')
        self.family_box = ttk.Combobox(field(row, '指标组', 0), textvariable=self.family, values=tuple(GROUPS), state='readonly', width=12)
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
        self.strength_button.grid(row=0, column=3, sticky='sw')
        self.current_selected = tk.BooleanVar(self)
        self.active_button = ttk.Checkbutton(row, text='用于抽取', variable=self.current_selected,
                                             command=self.toggle_current)
        self.active_button.grid(row=0, column=4, sticky='sw', padx=10)
        self.only_button = ttk.Button(row, text='只用这一项',
                                      command=lambda: indicator_selection.set((self.group.get(),)))
        self.only_button.grid(row=0, column=5, sticky='sw')
        row.columnconfigure(5, weight=1)
        self.mean = tk.StringVar(value='选择指标查看历史分布；双击次数回查开奖记录')
        wrapped_label(self, textvariable=self.mean, style='Muted.TLabel').pack(fill='x', pady=6)
        self.table = DataTable(self, WEIGHT_COLUMNS, (140, 105, 105, 125, 125, 125, 125))
        self.table.tree.configure(displaycolumns=CLASSIC_COLUMNS)
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
        wrapped_label(
            help_box.body,
            text='只有选中的指标才参与，默认一项也不选。单项只用该指标；多项按各项权重的强度次幂相乘。'
                 '未选的一侧等概率，强度和类别权重只影响所选项。理论占比以均匀组合为基准。'
                 '重邻孤按真实连续期计算；遗漏结构需连续 12 期参照。'
                 '后区复式按所有二码对子评分，含零权重对子则排除整组。权重是抽取偏好，不是中奖概率。',
            style='Muted.TLabel',
        ).pack(fill='x')
        self.draw_panel = StructureDrawPanel(self, inputs, draw)
        self.draw_panel.pack(side='bottom', before=help_box, fill='x', pady=(6, 0))
        self.period.trace_add('write', lambda *_: self.describe_pending())
        indicator_selection.summary.trace_add('write', self.reflect_selection)

    def reflect_selection(self, *_):
        self.current_selected.set(self.group.get() in self.indicator_selection.names)
        self.describe_pending()

    def toggle_current(self):
        self.indicator_selection.include(self.group.get(), self.current_selected.get())

    def select_family(self):
        names = GROUPS[self.family.get()]
        self.group_box.configure(values=names)
        self.group.set(names[0])
        self.render()

    def describe_pending(self):
        try:
            requested = self.periods()
        except ValueError as exc:
            pending, note = True, str(exc)
        else:
            pending = self.profile is not None and requested != self.profile.requested
            note = ('期数尚未应用；先统计并填入再抽取（会重置手动权重）' if pending
                    else '可输入自定义期数；重新统计会重置手动权重')
        self.pending.set(note)
        ready = self.profile is not None and not pending and not self._busy
        self.draw_panel.set_available(ready and bool(self.indicator_selection.names))
        self.use_button.configure(state='normal' if ready else 'disabled')

    def describe_selection(self):
        selected = self.table.selected()
        if len(selected) == 1:
            self.edit.set(selected[0][-1])

    def restore_group(self):
        if not self.profile:
            return
        new = deepcopy(self.profile)
        name = self.group.get()
        new.weights[name] = new.suggested_weights(name)
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
            if self.profile is None:
                self.table.set_rows(())
                self.mean.set('填入权重后可查看各指标的实际分布')
                self.summary.set(f'未填入权重：{exc}')
                self.describe_pending()
            self.error(exc)
            return
        self.profile = profile
        self.describe()
        self.render()
        self.on_change(profile)

    def describe(self):
        profile = self.profile
        first, last = profile.draws[0], profile.draws[-1]
        scope = f'近 {profile.requested} 期' if profile.requested else '全部'
        self.summary.set(f'已填入：{scope} · 实际 {len(profile.draws)} 期 · {first.issue or first.line} → {last.issue or last.line} · {profile.order}')
        self.describe_pending()

    def render(self):
        self.current_selected.set(self.group.get() in self.indicator_selection.names)
        if not self.profile: return
        p, name = self.profile, self.group.get()
        strength = p.strengths[name]
        self.strength.set(f'{strength:g}')
        average = p.means.get(name)
        indicator = INDICATORS.get(name)
        if indicator:
            description = indicator.description
            if name in TEMPORAL_INDICATORS:
                supported = indicator.codes(p.reference) is not None and p.samples(name)
                description += (f'；抽取参照第 {p.reference.issue} 期' if supported
                                else '；连续开奖不足，暂不能用于抽取')
                description += '；理论占比按有效样本的各期参照计算'
            else:
                description += '；理论占比按均匀组合计算'
        elif name.endswith('空区') or '中间覆盖' in name:
            description = '0=未发生，1=发生；均值即发生比例'
        elif name == '连号形态':
            description = '连续段长度组合：2+2+1 表示两组二连号加一个单号；1+1+1+1+1 表示无连号'
        else:
            description = 'C1–C4为排序后相邻号码差；最大跨区保留差值>7定义，起始跨区为最小号码分区减1'
        if isinstance(average, tuple):
            prefix = '平均每期：' + '、'.join(f'{part} {value:.2f}' for part, value in zip(indicator.parts, average)) + '；'
        else:
            prefix = f'历史均值：{average:.4f}；' if average is not None else ''
        self.mean.set(prefix + description)
        total = p.samples(name)
        baseline = p.baseline(name)
        suggestions = p.suggested_weights(name)
        self.table.tree.configure(displaycolumns=WEIGHT_COLUMNS if indicator else CLASSIC_COLUMNS)
        self.table.set_rows(
            (str(k), p.counts[name][k], total, f'{100*p.counts[name][k]/total:.4f}%' if total else '—',
             f'{100*baseline[k]:.4f}%' if baseline else '—', f'{suggestions[k]:.4f}' if total else '—',
             f'{p.weights[name][k]:.4f}')
            for k in domains()[name]
        )

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
        self._busy = busy
        for widget in (self.rebuild_button,self.strength_button,self.edit_button,self.period_box,self.restore_button,self.strength_entry,self.edit_entry,self.active_button,self.only_button):
            widget.configure(state='disabled' if busy else 'normal')
        for widget in (self.family_box, self.group_box):
            widget.configure(state='disabled' if busy else 'readonly')
        self.describe_pending()

"""随机参数表单；常用参数优先，固定/排除与跨区编辑按需展开。"""
import tkinter as tk
from tkinter import ttk
from ..core.generation import GenerationConfig, MODES
from ..core.models import parse_numbers
from .widgets import field, wrapped_label, Disclosure


class GenerationControls(ttk.Frame):
    def __init__(self, parent, generate):
        super().__init__(parent, padding=10)
        self.values = {}
        self.on_structure = lambda: None
        row = ttk.Frame(self)
        row.pack(fill="x")
        self.mode = tk.StringVar(value=MODES[0])
        self.mode_box = ttk.Combobox(field(row, "随机模式", 0), textvariable=self.mode,
                                     values=MODES, state="readonly", width=18)
        self.mode_box.pack(fill="x")
        for i, (name, default) in enumerate((("组数", "1"), ("前区数量", "5"), ("后区数量", "2")), 1):
            self.values[name] = tk.StringVar(value=default)
            ttk.Entry(field(row, name, i), textvariable=self.values[name], width=8).pack(fill="x")
        self.generate_button = ttk.Button(row, text="生成号码", command=generate, style="Primary.TButton")
        row.columnconfigure(4, weight=1)
        self.generate_button.grid(row=0, column=4, sticky="se")
        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=(6, 0))
        self.unique = tk.BooleanVar(value=True)
        ttk.Checkbutton(actions, text="本批组合不重复", variable=self.unique).pack(side="left")
        self.structure_button = ttk.Button(actions, text="结构权重设置", command=lambda: self.on_structure())
        self.structure_button.pack(side="right")
        self.custom = tk.BooleanVar(value=False)
        self.custom_button = ttk.Checkbutton(actions, text="自定义跨区权重", variable=self.custom, command=self.update_mode)
        self.custom_button.pack(side="right", padx=16)
        self.constraints = Disclosure(self, "固定 / 排除", toolbar=actions)
        self.constraints.pack(fill="x")
        for i, name in enumerate(("前区固定", "后区固定", "前区排除", "后区排除")):
            self.values[name] = tk.StringVar(value="")
            ttk.Entry(field(self.constraints.body, name, i, 1), textvariable=self.values[name], width=13).pack(fill="x")
            self.values[name].trace_add("write", self.describe_constraints)
        self.constraint_summary = tk.StringVar(value="不限制号码；多个号码可用空格或逗号分隔")
        wrapped_label(self, textvariable=self.constraint_summary, style="Muted.TLabel").pack(fill="x", pady=(4, 0))
        self.advanced = ttk.Frame(self, padding=(0, 10, 0, 0))
        fill_row = ttk.Frame(self.advanced)
        fill_row.pack(fill="x", pady=(0, 8))
        ttk.Label(fill_row, text="跨区权重来源").pack(side="left")
        self.cross_period = tk.StringVar(value="跟随结构权重页")
        self.cross_period_box = ttk.Combobox(fill_row, textvariable=self.cross_period,
                                            values=("跟随结构权重页", "50", "100", "全部"), width=18)
        self.cross_period_box.pack(side="left", padx=8)
        self.fill_button = ttk.Button(fill_row, text="一键填入")
        self.fill_button.pack(side="left")
        self.cross_source = tk.StringVar(value="可输入自定义期数；与结构页共用权重")
        wrapped_label(self.advanced, textvariable=self.cross_source, style="Muted.TLabel").pack(fill="x", pady=(0, 6))
        weights_row = ttk.Frame(self.advanced)
        weights_row.pack(fill="x")
        self.weight_vars = []
        for label in ("最大跨区", "起始跨区"):
            group = ttk.Frame(weights_row)
            group.pack(side="left", padx=(0, 22))
            ttk.Label(group, text=label).pack(side="left", padx=(0, 8))
            variables = []
            for i in range(5):
                ttk.Label(group, text=str(i)).pack(side="left", padx=(3, 2))
                var = tk.StringVar(value="1")
                ttk.Entry(group, textvariable=var, width=4).pack(side="left")
                variables.append(var)
            self.weight_vars.append(variables)
        self.hint = wrapped_label(self, text="", style="Muted.TLabel")
        self.hint.pack(fill="x", pady=(4, 0))
        self.mode_box.bind("<<ComboboxSelected>>", lambda _: self.update_mode())
        self.update_mode()

    def describe_constraints(self, *_):
        names = ("前区固定", "后区固定", "前区排除", "后区排除")
        active = [f"{name}：{self.values[name].get().strip()}" for name in names if self.values[name].get().strip()]
        self.constraint_summary.set(" · ".join(active) if active else "不限制号码；多个号码可用空格或逗号分隔")

    def update_mode(self):
        structure = self.mode.get() == MODES[2]
        self.custom_button.configure(state="normal" if structure else "disabled")
        if structure and self.custom.get():
            self.advanced.pack(fill="x", before=self.hint)
        else:
            self.advanced.pack_forget()
        hints = {
            MODES[0]: "系统随机源 · 合法组合等概率；固定或排除后在剩余组合中抽取。",
            MODES[1]: "使用结构权重页所选期数的号码次数 + 1 加权；历史频率不代表下期概率。",
            MODES[2]: "前区限5个 · 使用结构页的差值、连号、空区与跨区设置；跨区权重只计算一次。",
        }
        self.hint.configure(text=hints[self.mode.get()])

    def snapshot(self):
        v = self.values
        try:
            count, front, back = (int(v[n].get()) for n in ("组数", "前区数量", "后区数量"))
            weights = [tuple(float(var.get()) for var in group) for group in self.weight_vars] if self.mode.get() == MODES[2] and self.custom.get() else [(), ()]
        except ValueError as error:
            raise ValueError("组数与号码数量须为整数，跨区权重须为数值") from error
        config = GenerationConfig(count, front, back,
            parse_numbers(v["前区固定"].get(), 35, "前区固定"), parse_numbers(v["后区固定"].get(), 12, "后区固定"),
            parse_numbers(v["前区排除"].get(), 35, "前区排除"), parse_numbers(v["后区排除"].get(), 12, "后区排除"),
            self.mode.get(), self.unique.get(), weights[0], weights[1])
        config.validate()
        return config

"""随机参数表单；生成前读取快照，后台不访问 Tk 变量。"""
import tkinter as tk
from tkinter import ttk
from ..core.generation import GenerationConfig, MODES
from ..core.models import parse_numbers


class GenerationControls(ttk.Frame):
    def __init__(self, parent, generate):
        super().__init__(parent)
        self.values = {}
        defaults = {"组数": "1", "前区数量": "5", "后区数量": "2",
                    "前区固定": "", "后区固定": "", "前区排除": "", "后区排除": ""}
        row = ttk.Frame(self)
        row.pack(fill="x", pady=3)
        ttk.Label(row, text="随机模式").pack(side="left")
        self.mode = tk.StringVar(value=MODES[0])
        self.mode_box = ttk.Combobox(row, textvariable=self.mode, values=MODES, state="readonly", width=15)
        self.mode_box.pack(side="left", padx=(8, 15))
        for name in ("组数", "前区数量", "后区数量"):
            ttk.Label(row, text=name).pack(side="left", padx=(0, 4))
            self.values[name] = tk.StringVar(value=defaults[name])
            ttk.Entry(row, textvariable=self.values[name], width=6).pack(side="left", padx=(0, 12))
        self.generate_button = ttk.Button(row, text="重新随机", command=generate, style="Primary.TButton")
        self.generate_button.pack(side="right")
        row = ttk.Frame(self)
        row.pack(fill="x", pady=6)
        for name in ("前区固定", "后区固定", "前区排除", "后区排除"):
            ttk.Label(row, text=name).pack(side="left", padx=(0, 4))
            self.values[name] = tk.StringVar(value="")
            ttk.Entry(row, textvariable=self.values[name], width=13).pack(side="left", padx=(0, 12))
        row = ttk.Frame(self)
        row.pack(fill="x", pady=3)
        self.unique = tk.BooleanVar(value=True)
        ttk.Checkbutton(row, text="本批组合不重复", variable=self.unique).pack(side="left")
        ttk.Label(row, text="固定/排除可留空，多个号码用空格或逗号分隔。", style="Muted.TLabel").pack(side="left", padx=15)
        self.custom = tk.BooleanVar(value=False)
        self.custom_button = ttk.Checkbutton(row, text="自定义跨区权重", variable=self.custom, command=self.update_mode)
        self.custom_button.pack(side="right")
        self.advanced = ttk.Frame(self)
        self.weight_vars = []
        for label in ("最大跨区", "起始跨区"):
            group = ttk.Frame(self.advanced)
            group.pack(side="left", padx=(0, 22))
            ttk.Label(group, text=label).pack(side="left", padx=(0, 8))
            variables = []
            for i in range(5):
                ttk.Label(group, text=str(i)).pack(side="left", padx=(3, 2))
                var = tk.StringVar(value="1")
                ttk.Entry(group, textvariable=var, width=4).pack(side="left")
                variables.append(var)
            self.weight_vars.append(variables)
        self.hint = ttk.Label(self, text="", style="Muted.TLabel", wraplength=1050)
        self.hint.pack(fill="x", pady=(5, 8))
        self.mode_box.bind("<<ComboboxSelected>>", lambda _: self.update_mode())
        self.update_mode()

    def update_mode(self):
        structure = self.mode.get() == MODES[2]
        self.custom_button.configure(state="normal" if structure else "disabled")
        if structure and self.custom.get():
            self.advanced.pack(fill="x", before=self.hint, pady=6)
        else:
            self.advanced.pack_forget()
        hints = {
            MODES[0]: "系统随机源 · 合法组合等概率；固定或排除后，在剩余组合中等概率抽取。",
            MODES[1]: "使用已导入记录的号码次数 + 1 作为权重；历史频率不代表下期中奖概率。",
            MODES[2]: "前区限 5 个。综合号码、差值、连号、空区和跨区的历史权重；自定义值为相对权重，0 表示排除，不承诺最终占比。",
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

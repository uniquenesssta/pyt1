"""结构权重页的抽取参数区，沿用主选号页的输入。"""
from tkinter import ttk

from .number_constraints import NumberConstraints
from .widgets import wrapped_label


class StructureDrawPanel(ttk.LabelFrame):
    def __init__(self, parent, inputs, draw):
        super().__init__(parent, text="按当前权重抽取", padding=(8, 4))
        row = ttk.Frame(self)
        row.pack(fill="x")
        self.draw_button = ttk.Button(row, text="开始抽取", command=draw,
                                      style="Primary.TButton", state="disabled")
        self.draw_button.pack(side="right")
        ttk.Label(row, text="组数").pack(side="left")
        self.count_entry = ttk.Entry(row, textvariable=inputs.values["组数"], width=7)
        self.count_entry.pack(side="left", padx=(4, 12))
        ttk.Label(row, text="前区 5 个").pack(side="left", padx=(0, 12))
        ttk.Label(row, text="后区数量").pack(side="left")
        self.back_entry = ttk.Entry(row, textvariable=inputs.values["后区数量"], width=5)
        self.back_entry.pack(side="left", padx=(4, 12))
        ttk.Checkbutton(row, text="本批不重复", variable=inputs.unique).pack(side="left")
        self.constraints = NumberConstraints(self, row, inputs)
        self.constraints.pack(fill="x")
        wrapped_label(self, textvariable=inputs.summary, style="Muted.TLabel").pack(fill="x", pady=(4, 0))

    def set_available(self, available):
        self.draw_button.configure(state="normal" if available else "disabled")

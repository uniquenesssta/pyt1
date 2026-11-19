"""两页共用的加权选择，以及选号主页的单选、组合控件。"""
import tkinter as tk
from tkinter import ttk

from .indicator_groups import GROUPS
from .widgets import wrapped_label


class IndicatorSelection:
    def __init__(self, master):
        self.names = ()
        self.summary = tk.StringVar(master, value="未选加权指标")

    def set(self, names):
        self.names = tuple(dict.fromkeys(names))
        self.summary.set(f"本次加权（{len(self.names)} 项）：{'、'.join(self.names)}"
                         if self.names else "未选加权指标")

    def include(self, name, selected):
        if selected:
            self.set(self.names + (name,))
        else:
            self.set(n for n in self.names if n != name)


class IndicatorPicker(ttk.LabelFrame):
    def __init__(self, parent, selection):
        super().__init__(parent, text="本次加权指标", padding=(8, 4))
        self.selection = selection
        row = ttk.Frame(self)
        row.pack(fill="x")
        self.family = tk.StringVar(self, value="前区形态")
        self.metric = tk.StringVar(self, value=GROUPS["前区形态"][0])
        self.selected = tk.BooleanVar(self)
        family = ttk.Combobox(row, textvariable=self.family, values=tuple(GROUPS), width=12, state="readonly")
        family.pack(side="left")
        family.bind("<<ComboboxSelected>>", lambda _: self.change_group())
        self.metrics = ttk.Combobox(row, textvariable=self.metric, values=GROUPS["前区形态"],
                                    width=22, state="readonly")
        self.metrics.pack(side="left", padx=(6, 8))
        self.metrics.bind("<<ComboboxSelected>>", lambda _: self.reflect_choice())
        ttk.Checkbutton(row, text="用于抽取", variable=self.selected, command=self.toggle).pack(side="left")
        self.only_button = ttk.Button(row, text="只用这一项", command=lambda: selection.set((self.metric.get(),)))
        self.only_button.pack(side="left", padx=8)
        ttk.Button(row, text="清空选择", command=lambda: selection.set(())).pack(side="left")
        wrapped_label(self, textvariable=selection.summary, style="Muted.TLabel").pack(fill="x", pady=(4, 0))
        selection.summary.trace_add("write", self.reflect_choice)

    def change_group(self):
        options = GROUPS[self.family.get()]
        self.metrics.configure(values=options)
        self.metric.set(options[0])
        self.reflect_choice()

    def reflect_choice(self, *_):
        self.selected.set(self.metric.get() in self.selection.names)

    def toggle(self):
        self.selection.include(self.metric.get(), self.selected.get())

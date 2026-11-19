"""帖子选号模式的参数；条件频次的参照期和窗口在两个页面共用。"""
import tkinter as tk
from tkinter import ttk

from ..core.calendar_samples import CalendarRequest, WEEKDAY_LABELS
from .widgets import field


class CalendarControls(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.target = tk.StringVar(self)
        self.weekday = tk.StringVar(self, value="自动")
        self.recent = tk.StringVar(self, value="9")
        self.years = tk.StringVar(self, value="9")
        ttk.Entry(field(self, "目标期号（留空推下期）", 0), textvariable=self.target,
                  width=12).pack(fill="x")
        ttk.Combobox(field(self, "开奖星期", 1), textvariable=self.weekday, state="readonly",
                     values=("自动", *WEEKDAY_LABELS.values()), width=8).pack(fill="x")
        ttk.Entry(field(self, "同星期次数", 2), textvariable=self.recent, width=6).pack(fill="x")
        ttk.Entry(field(self, "历年同期年数", 3), textvariable=self.years, width=6).pack(fill="x")

    def snapshot(self):
        try:
            recent, years = int(self.recent.get()), int(self.years.get())
        except ValueError as error:
            raise ValueError("同星期次数和历年同期年数须为整数；0 表示跳过") from error
        weekday = next((day for day, label in WEEKDAY_LABELS.items() if label == self.weekday.get()), None)
        request = CalendarRequest(self.target.get().strip(), weekday, recent, years)
        request.validate()
        return request


class ConditionalInputs:
    def __init__(self, master):
        self.anchor = tk.StringVar(master)
        self.periods = tk.StringVar(master, value="全部")
        self.front = tk.BooleanVar(master, value=True)
        self.back = tk.BooleanVar(master, value=True)

    def snapshot(self):
        anchor = self.anchor.get().strip()
        value = self.periods.get().strip()
        if value == "全部":
            return anchor, 0
        try:
            periods = int(value)
            if periods < 1:
                raise ValueError
        except ValueError as error:
            raise ValueError("历史范围请选择全部，或输入正整数期数") from error
        return anchor, periods

    def selected_zones(self):
        return self.front.get(), self.back.get()


def conditional_fields(parent, inputs):
    ttk.Entry(field(parent, "参照期号（留空用最新）", 0), textvariable=inputs.anchor,
              width=12).pack(fill="x")
    ttk.Combobox(field(parent, "历史范围（期）", 1), textvariable=inputs.periods,
                 values=("全部", "50", "100"), width=8).pack(fill="x")


class ConditionalControls(ttk.Frame):
    def __init__(self, parent, inputs, open_analysis):
        super().__init__(parent)
        self.inputs = inputs
        conditional_fields(self, inputs)
        for column, (label, selected) in enumerate(
                (("前区 Top 5 票数", inputs.front), ("后区整对频次", inputs.back)), 2):
            ttk.Checkbutton(self, text=label, variable=selected).grid(row=0, column=column, sticky="sw",
                                                                    padx=(0, 10))
        ttk.Button(self, text="查看分析", command=open_analysis).grid(row=0, column=4, sticky="sw")

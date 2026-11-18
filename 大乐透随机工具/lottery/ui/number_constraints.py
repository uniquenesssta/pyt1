"""可在两个页面编辑同一套固定、排除号码。"""
from tkinter import ttk

from .selection_inputs import NUMBER_FIELDS
from .widgets import Disclosure, field


class NumberConstraints(Disclosure):
    def __init__(self, parent, toolbar, inputs):
        super().__init__(parent, "固定 / 排除", toolbar=toolbar)
        for column, name in enumerate(NUMBER_FIELDS):
            ttk.Entry(field(self.body, name, column, 1), textvariable=inputs.values[name],
                      width=13).pack(fill="x")

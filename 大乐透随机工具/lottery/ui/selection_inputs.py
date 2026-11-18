"""两个选号入口共用的参数和校验。"""
import tkinter as tk

from ..core.generation import GenerationConfig
from ..core.models import parse_numbers


COUNT_FIELDS = (("组数", "1"), ("前区数量", "5"), ("后区数量", "2"))
NUMBER_FIELDS = ("前区固定", "后区固定", "前区排除", "后区排除")


class SelectionInputs:
    def __init__(self, master):
        self.values = {name: tk.StringVar(master, value=default) for name, default in COUNT_FIELDS}
        self.values.update({name: tk.StringVar(master) for name in NUMBER_FIELDS})
        self.unique = tk.BooleanVar(master, value=True)
        self.summary = tk.StringVar(master)
        for name in NUMBER_FIELDS:
            self.values[name].trace_add("write", self.describe_constraints)
        self.describe_constraints()

    def describe_constraints(self, *_):
        active = [f"{name}：{self.values[name].get().strip()}" for name in NUMBER_FIELDS
                  if self.values[name].get().strip()]
        self.summary.set(" · ".join(active) if active else "不限制号码；多个号码可用空格或逗号分隔")

    def snapshot(self, mode, *, front_count=None):
        values = self.values
        try:
            count, back = int(values["组数"].get()), int(values["后区数量"].get())
            front = int(values["前区数量"].get()) if front_count is None else front_count
        except ValueError as error:
            raise ValueError("组数与号码数量须为整数") from error
        config = GenerationConfig(
            count=count, front_count=front, back_count=back, mode=mode, unique=self.unique.get(),
            front_fixed=parse_numbers(values["前区固定"].get(), 35, "前区固定"),
            back_fixed=parse_numbers(values["后区固定"].get(), 12, "后区固定"),
            front_excluded=parse_numbers(values["前区排除"].get(), 35, "前区排除"),
            back_excluded=parse_numbers(values["后区排除"].get(), 12, "后区排除"),
        )
        config.validate()
        return config

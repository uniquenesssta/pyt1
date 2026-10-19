"""维护显示状态；布局和摇卦控制器分别位于独立模块。"""
import tkinter as tk

from .layout import build_layout


class LiuYaoWindow:
    def __init__(self, master):
        self.master = master
        master.title("六爻摇卦（含说明）")
        master.geometry("820x800")
        master.minsize(720, 520)
        master.configure(bg="#f0f0f0")
        self.original_symbols = [tk.StringVar(master, value="未摇") for _ in range(6)]
        self.original_names = [tk.StringVar(master) for _ in range(6)]
        self.changed_symbols = [tk.StringVar(master) for _ in range(6)]
        self.changed_title = tk.StringVar(master, value="之卦（变化结果）")
        build_layout(self)

    def bind_start(self, callback):
        self.start_button.configure(command=callback)

    def reset(self):
        self.changed_title.set("之卦（变化结果）")
        for index in range(6):
            self.original_symbols[index].set("摇动中…")
            self.original_names[index].set("")
            self.changed_symbols[index].set("")

    def set_casting(self, casting):
        self.start_button.configure(
            state=tk.DISABLED if casting else tk.NORMAL,
            text="摇卦中…" if casting else "开始摇卦",
            bg="#9e9e9e" if casting else "#4caf50",
        )

    def show_rolling(self, index, symbol):
        self.original_symbols[index].set(symbol)

    def show_line(self, index, line):
        self.original_symbols[index].set(line.symbol)
        state = "动爻" if line.is_changing else "静爻"
        self.original_names[index].set(f"{line.name} · {state}")

    def show_result(self, hexagram):
        state = "有变爻" if hexagram.has_changes else "无变爻"
        self.changed_title.set(f"之卦（{state}）")
        for index, symbol in enumerate(hexagram.changed_symbols):
            self.changed_symbols[index].set(symbol)

"""维护显示状态；布局和摇卦控制器分别位于独立模块。"""
import tkinter as tk

from ..domain.text import format_changed, format_original
from .layout import build_layout


class LiuYaoWindow:
    def __init__(self, master, catalog=None):
        self.master = master
        self.catalog = catalog
        self._on_result = None
        self._on_reset = None
        master.title("六爻摇卦 · 本地参考解读")
        width = max(820, min(1000, master.winfo_screenwidth() - 80))
        height = max(640, min(900, master.winfo_screenheight() - 100))
        master.geometry(f"{width}x{height}")
        master.minsize(820, 640)
        master.configure(bg="#f0f0f0")
        self.original_symbols = [tk.StringVar(master, value="未摇") for _ in range(6)]
        self.original_names = [tk.StringVar(master) for _ in range(6)]
        self.changed_symbols = [tk.StringVar(master) for _ in range(6)]
        self.changed_title = tk.StringVar(master, value="之卦（变化结果）")
        self.original_hex_name = tk.StringVar(master, value="等待起卦")
        self.changed_hex_name = tk.StringVar(master, value="等待起卦")
        self._result = None
        build_layout(self)

    def bind_start(self, callback):
        self.start_button.configure(command=callback)

    def bind_result(self, on_result, on_reset):
        self._on_result = on_result
        self._on_reset = on_reset

    def reset(self):
        self._result = None
        self.original_copy_button.configure(state=tk.DISABLED, text="复制本卦")
        self.changed_copy_button.configure(state=tk.DISABLED, text="复制之卦")
        self.changed_title.set("之卦（变化结果）")
        self.original_hex_name.set("等待起卦")
        self.changed_hex_name.set("等待起卦")
        for index in range(6):
            self.original_symbols[index].set("摇动中…")
            self.original_names[index].set("")
            self.changed_symbols[index].set("")
        if self._on_reset is not None:
            self._on_reset()

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
        self._result = hexagram
        if self.catalog is not None:
            self.original_hex_name.set(self.catalog.identify(hexagram).display_name)
            self.changed_hex_name.set(self.catalog.identify(hexagram, changed=True).display_name)
        self.original_copy_button.configure(state=tk.NORMAL, text="复制本卦")
        self.changed_copy_button.configure(state=tk.NORMAL, text="复制之卦")
        if self._on_result is not None:
            self._on_result(hexagram)

    def copy_original(self):
        self._copy_result(lambda result: format_original(result, self.original_hex_name.get()),
                          self.original_copy_button)

    def copy_changed(self):
        self._copy_result(lambda result: format_changed(result, self.changed_hex_name.get()),
                          self.changed_copy_button)

    def _copy_result(self, formatter, button):
        if self._result is None:
            return
        text = formatter(self._result)
        self.master.clipboard_clear()
        self.master.clipboard_append(text)
        button.configure(text="已复制")

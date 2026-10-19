"""问题、背景与分标签展示的参考解读界面。"""
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from .instructions import build_instructions


class ReadingPanel:
    def __init__(self, parent, fonts):
        self._on_change = None
        frame = tk.Frame(parent, bg="#f0f0f0")
        frame.pack(fill=tk.BOTH, expand=True)
        form = tk.Frame(frame, bg="#f0f0f0")
        form.pack(fill=tk.X, pady=(0, 6))
        form.columnconfigure(1, weight=1)
        tk.Label(form, text="想问的事", bg="#f0f0f0", font=fonts["normal"]).grid(
            row=0, column=0, sticky="nw", padx=(0, 8), pady=3)
        self.question = tk.StringVar(parent)
        ttk.Entry(form, textvariable=self.question, font=fonts["normal"]).grid(
            row=0, column=1, sticky="ew", pady=(0, 5))
        tk.Label(form, text="补充背景", bg="#f0f0f0", font=fonts["normal"]).grid(
            row=1, column=0, sticky="nw", padx=(0, 8), pady=3)
        self.background = ScrolledText(form, height=2, wrap=tk.WORD, font=fonts["normal"],
                                       relief=tk.GROOVE, borderwidth=1, undo=True)
        self.background.grid(row=1, column=1, sticky="ew")

        actions = tk.Frame(frame, bg="#f0f0f0")
        actions.pack(fill=tk.X, pady=(0, 6))
        self.read_button = ttk.Button(actions, text="解读当前卦", state=tk.DISABLED)
        self.read_button.pack(side=tk.LEFT)
        self.copy_button = ttk.Button(actions, text="复制解读", state=tk.DISABLED)
        self.copy_button.pack(side=tk.LEFT, padx=(8, 12))
        tk.Label(actions, text="本地参考 · 原文与推测分开展示", font=fonts["small"],
                 bg="#f0f0f0", fg="#555").pack(side=tk.LEFT)

        self.tabs = ttk.Notebook(frame)
        self.tabs.pack(fill=tk.BOTH, expand=True)
        self.reading_text = self._add_text_tab("参考解读", fonts)
        self.references_text = self._add_text_tab("卦辞爻辞", fonts)
        instructions = tk.Frame(self.tabs, bg="#f0f0f0")
        self.tabs.add(instructions, text="使用说明")
        build_instructions(instructions, fonts)
        self.question.trace_add("write", lambda *args: self._changed())
        self.background.bind("<<Modified>>", self._background_changed)

    def _add_text_tab(self, title, fonts):
        frame = ttk.Frame(self.tabs)
        self.tabs.add(frame, text=title)
        text = ScrolledText(frame, height=8, wrap=tk.WORD, font=fonts["normal"],
                            padx=10, pady=8, relief=tk.FLAT)
        text.pack(fill=tk.BOTH, expand=True)
        text.configure(state=tk.DISABLED)
        return text

    def bind_actions(self, generate, copy, changed):
        self.read_button.configure(command=generate)
        self.copy_button.configure(command=copy)
        self._on_change = changed

    def _changed(self):
        if self._on_change is not None:
            self._on_change()

    def _background_changed(self, event):
        if self.background.edit_modified():
            self.background.edit_modified(False)
            self._changed()

    def get_context(self):
        return self.question.get().strip(), self.background.get("1.0", "end-1c").strip()

    @staticmethod
    def _replace(widget, text):
        widget.configure(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert("1.0", text)
        widget.configure(state=tk.DISABLED)
        widget.yview_moveto(0)

    def clear(self):
        self._replace(self.reading_text, "填写想问的事和背景，再点击“开始摇卦”。也可以先起卦，之后补充问题。")
        self._replace(self.references_text, "起卦后显示本卦、之卦的卦辞、六爻爻辞与来源。")
        self.read_button.configure(state=tk.DISABLED)
        self.copy_button.configure(state=tk.DISABLED, text="复制解读")

    def show_stale(self):
        self._replace(self.reading_text, "问题或背景已修改。点击“解读当前卦”，用同一组卦象更新参考解读。")
        self.copy_button.configure(state=tk.DISABLED, text="复制解读")

    def show_report(self, reading, references):
        self._replace(self.reading_text, reading)
        self._replace(self.references_text, references)
        self.read_button.configure(state=tk.NORMAL)
        self.copy_button.configure(state=tk.NORMAL, text="复制解读")

    def show_copied(self):
        self.copy_button.configure(text="已复制")

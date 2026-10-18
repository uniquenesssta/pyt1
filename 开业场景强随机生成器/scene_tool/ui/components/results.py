"""Compact rows: every dimension stays visible, long values have full tooltips."""
from tkinter import ttk, font
from scene_tool.ui.components.compact_text import fit_text
from scene_tool.ui.components.tooltip import Tooltip


class ResultList(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill='both', expand=True)
        self.columnconfigure(0, weight=1)
        self.next_row = 0
        self.text_font = font.Font(family='Microsoft YaHei UI', size=10)

    def group(self, title):
        header = ttk.Frame(self)
        header.grid(row=self.next_row, column=0, sticky='ew', pady=(4, 2))
        ttk.Label(header, text=title, style='Section.TLabel').pack(side='left')
        ttk.Label(header, text='锁定').pack(side='right', padx=4)
        self.next_row += 1

    def result(self, label, variable, lock):
        row = ttk.Frame(self, style='Result.TFrame', padding=(6, 1))
        row.grid(row=self.next_row, column=0, sticky='nsew', pady=1)
        self.rowconfigure(self.next_row, weight=1, uniform='results')
        self.next_row += 1
        # Text requests never enlarge the row; its size comes from available space.
        row.pack_propagate(False)
        name = ttk.Label(row, text=label, style='Muted.TLabel', width=16, anchor='w')
        name.pack(side='left')
        ttk.Checkbutton(row, variable=lock, style='Result.TCheckbutton').pack(side='right')
        value = ttk.Label(row, style='Result.TLabel', justify='left', anchor='w')
        value.pack(side='left', fill='both', expand=True, padx=(4, 0))
        def update(*_):
            lines = max(1, value.winfo_height() // self.text_font.metrics('linespace'))
            value.configure(text=fit_text(variable.get(), value.winfo_width(), lines, self.text_font.measure))
        value.bind('<Configure>', update)
        trace = variable.trace_add('write', update)
        row.bind('<Destroy>', lambda event: variable.trace_remove('write', trace) if event.widget is row else None)
        for widget in (name, value):
            Tooltip(widget, lambda: f'{name.cget("text")}\n{variable.get()}')
        return name

"""Compact editable results with candidate pickers and independent locks."""
from tkinter import ttk
from scene_tool.ui.components.tooltip import Tooltip


class ResultList(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill='both', expand=True)
        self.columnconfigure(0, weight=1)
        self.next_row = 0

    def group(self, title):
        header = ttk.Frame(self)
        header.grid(row=self.next_row, column=0, sticky='ew', pady=(4, 2))
        ttk.Label(header, text=title, style='Section.TLabel').pack(side='left')
        ttk.Label(header, text='隐藏', width=5).pack(side='right')
        ttk.Label(header, text='锁定', width=5).pack(side='right')
        self.next_row += 1

    def result(self, label, variable, lock, choices=None, readonly=False, hidden=None, on_hide=None):
        row = ttk.Frame(self, style='Result.TFrame', padding=(6, 1))
        row.grid(row=self.next_row, column=0, sticky='nsew', pady=1)
        self.rowconfigure(self.next_row, weight=1, uniform='results')
        self.next_row += 1
        # Text requests never enlarge the row; its size comes from available space.
        row.pack_propagate(False)
        name = ttk.Label(row, text=label, style='Muted.TLabel', width=16, anchor='w')
        name.pack(side='left')
        if hidden is not None:
            ttk.Checkbutton(row, variable=hidden, command=on_hide, width=3,
                            style='Result.TCheckbutton').pack(side='right')
        ttk.Checkbutton(row, variable=lock, width=3, style='Result.TCheckbutton').pack(side='right')
        # Locking excludes random draws, but never prevents intentional editing.
        if choices is None:
            value = ttk.Entry(row, textvariable=variable, width=1)
        else:
            value = ttk.Combobox(row, textvariable=variable, values=choices,
                                 state='readonly' if readonly else 'normal',
                                 width=1, height=14)
        value.pack(side='left', fill='x', expand=True, padx=(4, 6))
        name.editor = value
        for widget in (name, value):
            Tooltip(widget, lambda: f'{name.cget("text")}\n{variable.get()}')
        return name


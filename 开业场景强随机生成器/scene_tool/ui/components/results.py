"""Compact editable results with candidate pickers and independent locks."""
from tkinter import ttk
from scene_tool.ui.components.tooltip import Tooltip
from scene_tool.ui.components.flag_column import flag_heading, flag_control, flag_cell


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
        flag_heading(header, '隐藏')
        flag_heading(header, '锁定')
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
            flag_control(row, hidden, on_hide)
        if lock is not None:
            flag_control(row, lock)
        else:
            flag_cell(row, 'Result.TFrame')
            flag_cell(row, 'Result.TFrame')
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


"""Scrollable, wrapping random results with optional locks; no candidate picker."""
import tkinter as tk
from tkinter import ttk


class ResultList(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill='both', expand=True)
        self.canvas = tk.Canvas(self, highlightthickness=0, bg='#f3f5fa', width=420)
        scroll = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)
        self.content = ttk.Frame(self.canvas, padding=(0, 0, 12, 12))
        self.item = self.canvas.create_window(0, 0, window=self.content, anchor='nw')
        self.labels = []
        self.width = None
        self.content.bind('<Configure>', self._region)
        self.canvas.bind('<Configure>', self._width)
        self.root = self.winfo_toplevel()
        self.wheel_id = self.root.bind('<MouseWheel>', self._wheel, add='+')
        self.bind('<Destroy>', self._destroy, add='+')

    def _region(self, _):
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def _width(self, event):
        if event.width == self.width:
            return
        self.width = event.width
        self.canvas.itemconfigure(self.item, width=event.width)
        for label in self.labels:
            label.configure(wraplength=max(160, event.width - 36))

    def _wheel(self, event):
        if not event.delta or not self.winfo_ismapped():
            return
        widget = self.winfo_containing(event.x_root, event.y_root)
        while widget is not None:
            if widget is self:
                self.canvas.yview_scroll(-int(event.delta / 120) or (-1 if event.delta > 0 else 1), 'units')
                return 'break'
            widget = getattr(widget, 'master', None)

    def _destroy(self, event):
        if event.widget is self and self.wheel_id:
            self.root.unbind('<MouseWheel>', self.wheel_id)
            self.wheel_id = None

    def group(self, title):
        ttk.Label(self.content, text=title, style='Section.TLabel').pack(anchor='w', pady=(12, 6))

    def result(self, label, variable, lock):
        row = ttk.Frame(self.content, style='Result.TFrame', padding=(12, 8))
        row.pack(fill='x', pady=(0, 6))
        header = ttk.Frame(row, style='Result.TFrame')
        header.pack(fill='x')
        name = ttk.Label(header, text=label, style='Muted.TLabel')
        name.pack(side='left')
        ttk.Checkbutton(header, text='锁定', variable=lock, style='Result.TCheckbutton').pack(side='right')
        value = ttk.Label(row, textvariable=variable, style='Result.TLabel', wraplength=380, justify='left')
        value.pack(fill='x', pady=(4, 0))
        self.labels.append(value)
        return name

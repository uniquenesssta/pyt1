"""页面共用的表单布局与可展开说明。"""
import tkinter as tk
from tkinter import ttk


def field(parent, label, column, weight=0):
    frame = ttk.Frame(parent)
    frame.grid(row=0, column=column, sticky='ew', padx=(0, 8))
    parent.columnconfigure(column, weight=weight)
    ttk.Label(frame, text=label, style='Muted.TLabel').pack(anchor='w', pady=(0, 3))
    return frame


def wrapped_label(parent, **kwargs):
    """Wrap to the actual available width, including at higher Windows DPI."""
    label = ttk.Label(parent, **kwargs)
    label.bind('<Configure>', lambda event: label.configure(wraplength=max(160, event.width)))
    return label


class Disclosure(ttk.Frame):
    def __init__(self, parent, title, toolbar=None):
        super().__init__(parent)
        self.title, self.opened = title, False
        self.toolbar = toolbar
        self.button = ttk.Button(toolbar if toolbar is not None else self, text='展开' + title, command=self.toggle)
        if toolbar is None:
            self.button.pack(anchor='w')
        else:
            self.button.pack(side='left', padx=(12, 0))
        self.body = ttk.Frame(self, padding=(0, 8, 0, 0))

    def toggle(self):
        self.opened = not self.opened
        if self.opened:
            self.body.pack(fill='x')
        else:
            self.body.pack_forget()
            if self.toolbar is not None:
                self.configure(height=1)
        self.button.configure(text=('收起' if self.opened else '展开') + self.title)


class FormViewport(ttk.Frame):
    """Cap long parameter forms so expanded options never push results off-screen."""
    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, background=ttk.Style(self).lookup('TFrame', 'background'), highlightthickness=0, height=240)
        self.scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky='nsew')
        self.columnconfigure(0, weight=1)
        self.body = ttk.Frame(self.canvas)
        self.window = self.canvas.create_window(0, 0, anchor='nw', window=self.body)
        self.canvas.bind('<Configure>', self.resize)
        self.body.bind('<Configure>', self.resize)
        parent.bind('<Configure>', self.resize, add='+')

    def resize(self, event=None):
        available = max(160, int(self.master.winfo_height() * .45))
        needed = self.body.winfo_reqheight()
        height = min(needed, available)
        if int(float(self.canvas['height'])) != height:
            self.canvas.configure(height=height)
        self.canvas.itemconfigure(self.window, width=self.canvas.winfo_width())
        self.canvas.configure(scrollregion=(0, 0, self.canvas.winfo_width(), needed))
        if needed > height:
            self.scrollbar.grid(row=0, column=1, sticky='ns')
        else:
            self.scrollbar.grid_remove()
            self.canvas.yview_moveto(0)

    def bind_controls(self):
        def attach(widget):
            widget.bind('<MouseWheel>', self.wheel, add='+')
            widget.bind('<Button-4>', self.wheel, add='+')
            widget.bind('<Button-5>', self.wheel, add='+')
            widget.bind('<FocusIn>', self.reveal, add='+')
            for child in widget.winfo_children():
                attach(child)
        attach(self.body)

    def wheel(self, event):
        if self.body.winfo_reqheight() <= self.canvas.winfo_height():
            return
        if getattr(event, 'num', None) in (4, 5):
            units = -1 if event.num == 4 else 1
        else:
            units = -1 if event.delta > 0 else 1
        self.canvas.yview_scroll(units * 3, 'units')
        return 'break'

    def reveal(self, event):
        height = self.body.winfo_reqheight()
        if height <= self.canvas.winfo_height():
            return
        top = event.widget.winfo_rooty() - self.body.winfo_rooty()
        bottom = top + event.widget.winfo_height()
        visible_top = self.canvas.canvasy(0)
        visible_bottom = visible_top + self.canvas.winfo_height()
        if top < visible_top:
            self.canvas.yview_moveto(max(0, top - 8) / height)
        elif bottom > visible_bottom:
            self.canvas.yview_moveto((bottom + 8 - self.canvas.winfo_height()) / height)


def initialize_split(panes, fraction):
    """Set the initial division from available space, then leave it user-adjustable."""
    def configure(event):
        if event.height < 100:
            return
        panes.sashpos(0, round(event.height * fraction))
        panes.unbind('<Configure>', binding)
    binding = panes.bind('<Configure>', configure, add='+')

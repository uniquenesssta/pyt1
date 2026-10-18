"""Full random text on hover, without expanding the compact result row."""
import tkinter as tk
from tkinter import ttk


class Tooltip:
    def __init__(self, widget, text):
        self.widget, self.text = widget, text
        self.pending = self.popup = None
        widget.bind('<Enter>', self.schedule, add='+')
        for event in ('<Leave>', '<ButtonPress>', '<Unmap>', '<Destroy>'):
            widget.bind(event, self.hide, add='+')

    def schedule(self, _):
        self.hide()
        self.pending = self.widget.after(450, self.show)

    def show(self):
        self.pending = None
        if not self.widget.winfo_ismapped():
            return
        self.popup = tk.Toplevel(self.widget)
        self.popup.overrideredirect(True)
        ttk.Label(self.popup, text=self.text(), wraplength=480, padding=12,
                  justify='left', relief='solid').pack()
        self.popup.update_idletasks()
        x = min(self.widget.winfo_rootx(), self.widget.winfo_screenwidth() - self.popup.winfo_reqwidth())
        y = min(self.widget.winfo_rooty() + self.widget.winfo_height(), self.widget.winfo_screenheight() - self.popup.winfo_reqheight())
        self.popup.geometry(f'+{max(0, x)}+{max(0, y)}')

    def hide(self, _=None):
        if self.pending is not None:
            self.widget.after_cancel(self.pending)
            self.pending = None
        if self.popup is not None:
            self.popup.destroy()
            self.popup = None

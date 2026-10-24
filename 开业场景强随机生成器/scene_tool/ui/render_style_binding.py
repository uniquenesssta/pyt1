"""Toolbar mode selection connected to active scene generation and storage."""
import tkinter as tk
from tkinter import ttk, messagebox
from scene_tool.config.render_styles import RENDER_STYLES


class RenderStyleSelector:
    def __init__(self, switcher, parent):
        self.switcher = switcher
        self.value = tk.StringVar()
        ttk.Label(parent, text='提示词风格').pack(side='left', padx=(24, 8))
        self.selector = ttk.Combobox(parent, textvariable=self.value,
                                     values=RENDER_STYLES, state='readonly', width=14)
        self.selector.pack(side='left')
        self.selector.bind('<<ComboboxSelected>>', self.change)
        self.sync()

    def sync(self):
        s = self.switcher
        style = s.window.render_style.get() if s.active == '开业场景' else s.models[s.active].render_style
        self.value.set(style)

    def change(self, _=None):
        s = self.switcher
        style = self.value.get()
        if s.active == '开业场景':
            view = s.window
            previous = view.render_style.get()
            if style == previous:
                return
            view.render_style.set(style)
            if not view.refresh(force=True):
                view.render_style.set(previous)
                self.sync()
                return
            view.prompt_reset.snapshot = None
            view.undo_reset_button.configure(state='disabled')
            view.save()
        else:
            panel = s.panels[s.active]
            if style == panel.model.render_style:
                return
            if not panel.allow_replace():
                self.sync()
                return
            previous = panel.model.render_style
            panel.model.render_style = style
            try:
                panel.model.regenerate()
            except ValueError as exc:
                panel.model.render_style = previous
                self.sync()
                messagebox.showerror('参数未完成', str(exc), parent=panel)
                return
            panel.model.undo = None
            panel.show_prompt()
            panel.persist()

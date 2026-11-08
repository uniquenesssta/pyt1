"""Visible strategy selector for the active scene; selection itself does not draw."""
import tkinter as tk
from tkinter import ttk
from scene_tool.config.random_strategy import STRATEGIES

class StrategySelector:
    def __init__(self, switcher, parent):
        self.switcher = switcher
        self.value = tk.StringVar()
        ttk.Label(parent,text='随机方式').pack(side='left',padx=(18,6))
        box = ttk.Combobox(parent,textvariable=self.value,values=STRATEGIES,state='readonly',width=12)
        box.pack(side='left')
        box.bind('<<ComboboxSelected>>',self.change)
        self.sync()

    def sync(self):
        s=self.switcher
        self.value.set(s.window.random_strategy.get() if s.active=='开业场景' else s.models[s.active].random_strategy)

    def change(self,_=None):
        s=self.switcher
        if s.active=='开业场景':
            s.window.random_strategy.set(self.value.get())
            s.window.save()
        else:
            s.models[s.active].random_strategy=self.value.get()
            s.persist()

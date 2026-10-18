"""One mode selector with independent panels and preserved per-scene state."""
import tkinter as tk
from tkinter import ttk, messagebox
from scene_tool.domain.scene_model import SceneModel
from scene_tool.storage.scenes import load_profiles, load_scene_states, save_scene_states
from scene_tool.ui.scenes.panel import ScenePanel


class SceneSwitcher:
    def __init__(self, window):
        self.window = window
        self.models, self.panels = {}, {}
        try:
            state = load_scene_states()
        except (OSError, ValueError) as exc:
            state = {}
            window.after_idle(lambda error=str(exc): messagebox.showwarning('场景设置读取失败', error, parent=window))
        for error in state.get('errors', []):
            window.after_idle(lambda e=error: messagebox.showwarning('场景设置读取失败', e, parent=window))
        self.profiles = {p['name']: p for p in load_profiles()}
        for name, profile in self.profiles.items():
            try:
                self.models[name] = SceneModel(profile, state.get('scenes', {}).get(name))
            except (TypeError, ValueError, AttributeError):
                window.after_idle(lambda mode=name: messagebox.showwarning('场景设置损坏', mode + '的设置无法恢复，已使用默认参数；其他场景不受影响。', parent=window))
                self.models[name] = SceneModel(profile)
        self.active = '开业场景'
        bar = ttk.Frame(window, padding=(24, 8))
        bar.place(x=0, y=0, relwidth=1, height=50)
        ttk.Label(bar, text='场景模式').pack(side='left', padx=(0, 12))
        self.selection = tk.StringVar(value='开业场景')
        choices = ['开业场景', *self.profiles]
        selector = ttk.Combobox(bar, textvariable=self.selection, values=choices, state='readonly', width=24)
        selector.pack(side='left')
        selector.bind('<<ComboboxSelected>>', self.switch)
        self.viewport = ttk.Frame(window)
        self.viewport.place(x=0, y=50, relwidth=1, relheight=1, height=-50)
        window.content_surface.place(in_=self.viewport, x=0, y=0, relwidth=1, relheight=1)
        window.content_surface.lift()
        window.resize_controller.surface = self.viewport
        window.resize_controller.height_offset = -50
        window.title('多场景强随机 · 手机实拍提示词')
        if state.get('active') in self.profiles:
            self.selection.set(state['active'])
            self.switch()

    def persist(self):
        for panel in self.panels.values():
            panel.capture()
        try:
            save_scene_states(self.active, self.models)
            return True
        except OSError as exc:
            messagebox.showerror('场景保存失败', str(exc), parent=self.window)
            return False

    def switch(self, *_):
        target = self.selection.get()
        if target == self.active:
            return
        if self.active == '开业场景':
            self.window.flush_refresh()
            if not self.window.save():
                self.selection.set(self.active)
                return
            self.window.content_surface.place_forget()
        else:
            self.panels[self.active].pause()
            self.panels[self.active].place_forget()
        self.active = target
        if target == '开业场景':
            self.window.content_surface.place(in_=self.viewport, x=0, y=0, relwidth=1, relheight=1)
            self.window.content_surface.lift()
        else:
            if target not in self.panels:
                self.panels[target] = ScenePanel(self.viewport, self.models[target], self.persist)
            self.panels[target].place(x=0, y=0, relwidth=1, relheight=1)
            self.panels[target].lift()
        self.persist()

    def save(self):
        for panel in self.panels.values():
            panel.pause()
        return self.persist()

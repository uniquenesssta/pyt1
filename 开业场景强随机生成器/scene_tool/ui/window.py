import tkinter as tk
from tkinter import messagebox
from scene_tool.config.defaults import DIMENSIONS
from scene_tool.config.render_styles import BUYER
from scene_tool.config.product_size import FOLLOW_REFERENCE
from scene_tool.config.paths import DATA
from scene_tool.generation.copywriting import CopyRandomizer
from scene_tool.generation.parameters import Randomizer
from scene_tool.storage.pools import load_startup_pools
from scene_tool.ui.theme import apply_theme
from scene_tool.ui.style_binding import sync_style, environment_changed
from scene_tool.ui.layout import build_ui
from scene_tool.ui.pool_editor import edit_pools
from scene_tool.ui.session_binding import save, restore
from scene_tool.ui.prompt_controller import PromptController
from scene_tool.ui.prompt_reset import PromptResetController
from scene_tool.ui.resize_controller import ResizeController
from scene_tool.ui.scenes.switcher import SceneSwitcher


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('12维强随机 · 开业场景提示词')
        self.geometry('1180x800')
        self.minsize(940, 660)
        apply_theme(self)
        self.values = {k: tk.StringVar() for k, _ in DIMENSIONS}
        self.locks = {k: tk.BooleanVar() for k, _ in DIMENSIONS}
        self.hidden = {k: tk.BooleanVar(value=False) for k in [*[key for key, _ in DIMENSIONS], 'copy']}
        self.product_size = tk.StringVar(value=FOLLOW_REFERENCE)
        self.render_style = tk.StringVar(value=BUYER)
        self.industry = tk.StringVar(value='美业')
        self.copy_random = tk.BooleanVar(value=True)
        self.copy_locked = tk.BooleanVar(value=False)
        self.copy_engine = CopyRandomizer()
        self.copyline = tk.StringVar(value='盛大开业 · 美好启幕')
        self.strong = tk.BooleanVar(value=True)
        self.generated_names = tk.BooleanVar(value=True)
        self.status = tk.StringVar(value='')
        self.rendered = ''
        self.ready = False
        self.pending = None
        self.pool_path = DATA / 'custom_pools.json'
        pools, self.startup_errors = load_startup_pools(self.pool_path)
        self.prompt_controller = PromptController(self)
        self.prompt_reset = PromptResetController(self)
        self.engine = Randomizer(pools)
        self.build_ui()
        self.restore()
        sync_style(self)
        if not self.edited():
            self.refresh()
        self.resize_controller = ResizeController(self, self.content_surface)
        self.ready = True
        for var in [*self.values.values(), self.industry, self.copyline, self.product_size]:
            var.trace_add('write', self.schedule_refresh)
        if not all(v.get() for v in self.values.values()):
            self.randomize()
        elif not self.prompt.get('1.0', 'end-1c'):
            self.refresh()
        self.values['environment'].trace_add('write', lambda *_: environment_changed(self))
        self.scene_switcher = SceneSwitcher(self)
        self.protocol('WM_DELETE_WINDOW', self.close)
        for error in self.startup_errors:
            self.after_idle(lambda e=error: messagebox.showwarning('读取设置', e, parent=self))

    def current(self):
        return {k: v.get().strip() for k, v in self.values.items()}

    def randomize(self):
        locked = [k for k, v in self.locks.items() if v.get()]
        if len(locked) == len(DIMENSIONS) and (not self.copy_random.get() or self.copy_locked.get()):
            self.status.set('参数已全部锁定，且文案随机已关闭或锁定，请解锁需要随机的项目。')
            return
        if self.edited() and not messagebox.askyesno('重新随机', '重新随机会生成新提示词，并替换右侧手动编辑。继续吗？', parent=self):
            return
        if self.pending:
            self.after_cancel(self.pending)
            self.pending = None
        self.engine.generated = self.generated_names.get()
        values = self.engine.draw(self.current(), locked, self.strong.get(), self.render_style.get())
        self.ready = False
        self.copyline.set(self.copy_engine.draw(self.copyline.get(), self.copy_random.get(), self.copy_locked.get()))
        for key, value in values.items():
            self.values[key].set(value)
        sync_style(self)
        self.ready = True
        self.rendered = self.prompt.get('1.0', 'end-1c')
        self.refresh()
        self.save()

    def unlock(self):
        for value in self.locks.values():
            value.set(False)
        self.copy_locked.set(False)
        self.status.set('已全部解锁。')

    def close(self):
        if not self.scene_switcher.save() and not messagebox.askyesno('场景保存失败', '场景设置未保存，仍要退出吗？', parent=self):
            return
        self.flush_refresh()
        if not self.save() and not messagebox.askyesno('设置保存失败', '无法保存当前设置，仍要退出吗？可以先复制或导出提示词。', parent=self):
            return
        self.destroy()

    def generated(self, *args, **kwargs):
        return self.prompt_controller.generated(*args, **kwargs)

    def edited(self, *args, **kwargs):
        return self.prompt_controller.edited(*args, **kwargs)

    def schedule_refresh(self, *args, **kwargs):
        return self.prompt_controller.schedule_refresh(*args, **kwargs)

    def refresh(self, *args, **kwargs):
        return self.prompt_controller.refresh(*args, **kwargs)

    def set_prompt(self, *args, **kwargs):
        return self.prompt_controller.set_prompt(*args, **kwargs)

    def copy_prompt(self, *args, **kwargs):
        return self.prompt_controller.copy_prompt(*args, **kwargs)

    def flush_refresh(self, *args, **kwargs):
        return self.prompt_controller.flush_refresh(*args, **kwargs)

    def export(self, *args, **kwargs):
        return self.prompt_controller.export(*args, **kwargs)

    def build_ui(self):
        return build_ui(self)

    def edit_pools(self):
        return edit_pools(self)

    def save(self):
        return save(self)

    def restore(self):
        return restore(self)


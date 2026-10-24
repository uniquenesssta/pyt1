from pathlib import Path
from tkinter import ttk, messagebox, filedialog
from scene_tool.ui.scenes.layout import build_panel
from scene_tool.ui.scenes.pool_editor import edit_pool


class ScenePanel(ttk.Frame):
    def __init__(self, parent, model, persist):
        super().__init__(parent, padding=20)
        self.model, self.persist = model, persist
        self.pending = None
        self.updating = False
        build_panel(self)
        for variable in self.values.values():
            variable.trace_add('write', self.schedule)
        self.extra.bind('<KeyRelease>', self.schedule)
        self.prompt.bind('<<Modified>>', self.prompt_changed)
        self.update_status()

    def update_status(self):
        edited = self.prompt.get('1.0', 'end-1c') != self.model.rendered
        self.sync_status.set('已手动编辑' if edited else ('待更新' if self.pending else '已同步'))

    def prompt_changed(self, _):
        if self.prompt.edit_modified():
            self.prompt.edit_modified(False)
            self.update_status()

    def capture(self):
        self.model.values = {k: v.get().strip() for k, v in self.values.items()}
        self.model.locks = {k: v.get() for k, v in self.locks.items()}
        self.model.hidden = {k: v.get() for k, v in self.hidden.items()}
        self.model.extra = self.extra.get('1.0', 'end-1c')
        self.model.prompt = self.prompt.get('1.0', 'end-1c')

    def pause(self):
        if self.pending is not None:
            self.after_cancel(self.pending)
            self.pending = None
        self.capture()

    def schedule(self, *_):
        if self.updating:
            return
        if self.pending is not None:
            self.after_cancel(self.pending)
        self.pending = self.after(250, self.auto_update)
        self.update_status()

    def auto_update(self):
        self.pending = None
        self.capture()
        if self.model.prompt == self.model.rendered:
            try:
                self.model.regenerate()
                self.show_prompt()
            except ValueError:
                pass

        self.update_status()

    def allow_replace(self):
        self.pause()
        return self.model.prompt == self.model.rendered or messagebox.askyesno('替换手改提示词', '按当前参数重新生成，将替换手动修改。继续吗？', parent=self)

    def show_prompt(self):
        if self.prompt.get('1.0', 'end-1c') != self.model.prompt:
            self.prompt.delete('1.0', 'end')
            self.prompt.insert('1.0', self.model.prompt)
        self.update_status()

    def randomize(self):
        if not self.allow_replace():
            return
        self.model.draw()
        self.updating = True
        for key, value in self.model.values.items():
            self.values[key].set(value)
        self.updating = False
        self.model.regenerate()
        self.show_prompt()
        self.persist()

    def update_prompt(self):
        if self.allow_replace():
            try:
                self.model.regenerate()
                self.show_prompt()
                self.persist()
            except ValueError as exc:
                messagebox.showerror('参数未完成', str(exc), parent=self)

    def copy(self):
        if self.pending is not None:
            self.after_cancel(self.pending)
            self.auto_update()
        self.clipboard_clear()
        self.clipboard_append(self.prompt.get('1.0', 'end-1c'))
        self.sync_status.set('已复制')
        self.persist()

    def export(self):
        if self.pending is not None:
            self.after_cancel(self.pending)
            self.auto_update()
        self.capture()
        path = filedialog.asksaveasfilename(parent=self, defaultextension='.txt', initialfile=self.model.profile['name'] + '提示词.txt')
        if path:
            try:
                Path(path).write_text(self.model.prompt, encoding='utf-8-sig')
            except OSError as exc:
                messagebox.showerror('导出失败', str(exc), parent=self)

    def reset(self):
        self.pause()
        try:
            self.model.reset()
        except ValueError as exc:
            messagebox.showerror('参数未完成', str(exc), parent=self)
            return
        self.extra.delete('1.0', 'end')
        self.show_prompt()
        self.persist()

    def undo_reset(self):
        self.pause()
        self.model.undo_reset()
        self.extra.delete('1.0', 'end')
        self.extra.insert('1.0', self.model.extra)
        self.show_prompt()
        self.persist()

    def unlock(self):
        for variable in self.locks.values():
            variable.set(False)
        self.persist()

    def edit_pools(self):
        edit_pool(self)


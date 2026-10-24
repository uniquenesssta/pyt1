from pathlib import Path
from tkinter import messagebox, filedialog
from scene_tool.domain.prompts import make_prompt
from scene_tool.domain.visibility import view_hidden

class PromptController:
    def __init__(self, view):
        self.view = view

    def generated(self):
        return make_prompt(self.view.current(), self.view.industry.get(), self.view.constraints.get('1.0', 'end-1c'),
                           self.view.copyline.get(), self.view.extra.get('1.0', 'end-1c'), hidden=view_hidden(self.view), render_style=self.view.render_style.get())

    def edited(self):
        return self.view.prompt.get('1.0', 'end-1c') != self.view.rendered

    def schedule_refresh(self, *_):
        if not self.view.ready:
            return
        if self.view.pending:
            self.view.after_cancel(self.view.pending)
        self.view.pending = self.view.after(250, self.refresh)

    def refresh(self, force=False):
        if self.view.pending:
            self.view.after_cancel(self.view.pending)
        self.view.pending = None
        if self.edited():
            if not force:
                self.view.status.set('提示词有手动编辑，已保留；参数变动后请点“更新提示词”重新组成，或直接复制当前文字。')
                return False
            if not messagebox.askyesno('更新提示词', '根据当前参数重新组成提示词，会替换右侧的手动编辑。继续吗？', parent=self.view):
                return False
        try:
            content = self.generated()
        except ValueError as exc:
            self.view.status.set(str(exc))
            return False
        self.set_prompt(content)
        self.view.status.set('提示词已更新。复制后与参考图一并提交；本工具离线运行，只生成文字。')
        return True

    def set_prompt(self, content):
        if self.view.prompt.get('1.0', 'end-1c') == content:
            self.view.rendered = content
            return
        self.view.prompt.delete('1.0', 'end')
        self.view.prompt.insert('1.0', content)
        self.view.rendered = content

    def copy_prompt(self):
        self.flush_refresh()
        text = self.view.prompt.get('1.0', 'end-1c')
        if not text.strip():
            return
        self.view.clipboard_clear()
        self.view.clipboard_append(text)
        self.view.update_idletasks()
        self.view.status.set('已复制当前完整提示词，可以粘贴并附上参考图。')

    def flush_refresh(self):
        if self.view.pending:
            self.view.after_cancel(self.view.pending)
            self.view.pending = None
            self.refresh()

    def export(self):
        self.flush_refresh()
        path = filedialog.asksaveasfilename(parent=self.view, title='导出提示词', defaultextension='.txt', initialfile='开业场景提示词.txt', filetypes=[('文本文件', '*.txt')])
        if path:
            try:
                Path(path).write_text(self.view.prompt.get('1.0', 'end-1c'), encoding='utf-8-sig')
                self.view.status.set(f'已导出：{path}')
            except OSError as exc:
                messagebox.showerror('导出失败', str(exc), parent=self.view)


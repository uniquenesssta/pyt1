"""预览右键单文件删除与后台执行。"""
import threading
import tkinter as tk
from tkinter import messagebox
from ..core.preview_delete import preview_file_path, delete_preview_file
from ..storage.recycle import recycle_file


class PreviewActionsMixin:
    def create_preview_menu(self):
        self.preview_menu = tk.Menu(self, tearoff=False)
        self.preview_menu.add_command(label='删除文件（移入回收站）', command=self.delete_preview_row)
        self.tree.bind('<Button-3>', self.open_preview_menu)
        self._context_plan = None

    def open_preview_menu(self, event):
        self.preview_menu.unpost()
        self._context_plan = None
        if self.busy:
            return
        if self.tree.identify_region(event.x, event.y) not in ('cell', 'tree'):
            return
        row = self.tree.identify_row(event.y)
        if not row or row not in self.tree.selection():
            return
        self._context_plan = self._preview_rows.get(row)
        if self._context_plan is None:
            return
        self.tree.focus(row)
        try:
            self.preview_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.preview_menu.grab_release()

    def delete_preview_row(self):
        plan = self._context_plan
        selected = [self._preview_rows.get(row) for row in self.tree.selection()]
        if self.busy or plan is None or not any(p is plan for p in selected) or not any(p is plan for p in self.plans):
            return
        try:
            path = preview_file_path(plan)
        except Exception as exc:
            messagebox.showerror('无法删除', str(exc), parent=self)
            return
        if not messagebox.askyesno('确认删除文件', f'将以下文件移入回收站：\n\n{path}\n\n是否继续？', parent=self):
            return
        self.set_busy(True)
        def worker():
            try:
                deleted = delete_preview_file(plan, recycle_file)
                self.work_queue.put(('delete_done', plan, deleted))
            except Exception as exc:
                self.work_queue.put(('error', f'删除失败：{path}\n{exc}'))
        self.worker = threading.Thread(target=worker, daemon=False)
        self.worker.start()

    def finish_preview_delete(self, plan, path):
        self.plans = [p for p in self.plans if p is not plan]
        self.scan_session = None
        self._context_plan = None
        self._insert_plan_rows()
        self.log(f'已移入回收站：{path}')
        self.set_busy(False)

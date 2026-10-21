"""预览右键单文件删除与后台执行。"""
import threading
import tkinter as tk
from tkinter import messagebox
from ..core.preview_delete import preview_file_path, delete_preview_files
from ..storage.recycle import recycle_file
from .delete_confirmation import confirm_delete


class PreviewActionsMixin:
    def create_preview_menu(self):
        self.preview_menu = tk.Menu(self, tearoff=False)
        self.preview_menu.add_command(label='删除文件（移入回收站）', command=self.delete_preview_row)
        self.tree.bind('<Button-3>', self.open_preview_menu)
        self.tree.bind('<Control-a>', self.select_all_preview)
        self.tree.bind('<Control-A>', self.select_all_preview)
        self._context_plan = None

    def select_all_preview(self, _event=None):
        if not self.busy:
            self.tree.selection_set(self.tree.get_children())
        return 'break'

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
        count = len(self.tree.selection())
        self.preview_menu.entryconfigure(0, label=f"删除选中的 {count} 个文件（移入回收站）")
        self.tree.focus(row)
        try:
            self.preview_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.preview_menu.grab_release()

    def delete_preview_row(self):
        plan = self._context_plan
        selected = [self._preview_rows.get(row) for row in self.tree.selection()]
        if self.busy or plan is None or not any(p is plan for p in selected):
            return
        plans = [p for p in selected if p is not None and any(current is p for current in self.plans)]
        if not plans:
            return
        try:
            paths = [preview_file_path(p) for p in plans]
        except Exception as exc:
            messagebox.showerror('无法删除', str(exc), parent=self)
            return
        if not confirm_delete(self, paths):
            return
        self.set_busy(True)
        def worker():
            try:
                succeeded, failed = delete_preview_files(plans, recycle_file)
                self.work_queue.put(('delete_batch_done', succeeded, failed))
            except Exception as exc:
                self.work_queue.put(('error', f'删除失败：{exc}'))
        self.worker = threading.Thread(target=worker, daemon=False)
        self.worker.start()

    def finish_preview_batch_delete(self, succeeded, failed):
        removed = {id(plan) for plan, _path in succeeded}
        self.plans = [p for p in self.plans if id(p) not in removed]
        if succeeded:
            self.scan_session = None
        self._context_plan = None
        for plan, path in succeeded:
            self.log(f'已移入回收站：{path}')
        for plan, reason in failed:
            self.log(f'删除失败：{preview_file_path(plan)}：{reason}')
        self._insert_plan_rows()
        self.set_busy(False)
        self.log(f'批量删除完成：成功 {len(succeeded)} 个，失败 {len(failed)} 个。')
        if failed:
            messagebox.showwarning('部分文件未删除', f'成功 {len(succeeded)} 个，失败 {len(failed)} 个。失败项保留在预览中，具体原因见日志。', parent=self)

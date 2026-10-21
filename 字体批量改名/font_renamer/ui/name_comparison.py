"""同名候选对比、保留选择和后台清理交互。"""
import copy
import queue
import threading
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from .name_comparison_layout import NameComparisonLayout
from ..core.same_names import clean_name_groups
from ..storage.recycle import recycle_file


class NameComparisonWindow(NameComparisonLayout, tk.Toplevel):
    def __init__(self,parent,session):
        super().__init__(parent)
        self.title('同名字体对比'); self.geometry('1250x650'); self.minsize(900,450)
        self.transient(parent); self.grab_set()
        self.groups=copy.deepcopy(session.name_groups); self.busy=False; self.events=queue.Queue()
        self.protocol('WM_DELETE_WINDOW',self.close)
        self.build(); self.after(100,self.poll); self.refresh()

    def close(self):
        if self.busy:
            messagebox.showinfo('正在处理','请等待任务完成。',parent=self); return
        self.destroy()

    def current(self):
        selected=self.groups_list.curselection()
        return self.groups[selected[0]] if selected else None

    def refresh(self):
        old=self.groups_list.curselection()
        self.groups_list.delete(0,'end')
        for i,g in enumerate(self.groups):
            self.groups_list.insert('end',f'{i+1}. {Path(g.members[0].path).stem} · {len(g.members)}份 · {g.status}')
        if self.groups:
            self.groups_list.selection_set(min(old[0] if old else 0,len(self.groups)-1))
        pending=sum(len(g.members)-1 for g in self.groups if g.keep and g.status=='待清理')
        self.summary.set(f'同名候选 {len(self.groups)} 组；已确认待清理 {pending} 个文件')
        self.clean_button.configure(state='normal' if pending and not self.busy else 'disabled')
        self.show_group()

    def show_group(self,_event=None):
        self.table.delete(*self.table.get_children()); self.notes.delete('1.0','end')
        g=self.current()
        self.keep_button.configure(state='normal' if g and not self.busy and g.status in ('待选择保留项','待清理') else 'disabled')
        if not g:return
        for i,m in enumerate(g.members):
            choice=('保留' if m.path==g.keep else '待清理') if g.keep else '待选择'
            self.table.insert('','end',iid=str(i),values=(choice,Path(m.path).name,m.full_name or '未读到',m.style,m.version,m.size,m.glyphs,m.characters,m.digest,m.path))
        identical=len({m.digest for m in g.members})==1
        self.notes.insert('end',('内容完全一致。' if identical else '同名但内容不同，请比较版本、样式、字形与字符数量后决定。')+'\n文件名（不含扩展名）或内部完整名称相同会归入候选组；未指定保留项的组不会清理。\n')
        for m in g.members:
            if m.error:self.notes.insert('end',f'{m.path}：读取信息失败：{m.error}\n')
        self.notes.insert('end','\n'.join(g.details))

    def choose_keep(self):
        g=self.current(); selected=self.table.selection()
        if self.busy or not g or g.status not in ('待选择保留项','待清理'):return
        if not selected:
            messagebox.showinfo('选择保留文件','先点击表格中要保留的文件，再点击此按钮。',parent=self);return
        g.keep=g.members[int(selected[0])].path; g.status='待清理'; self.refresh()

    def reset_group(self):
        g=self.current()
        if self.busy or not g or g.status not in ('待选择保留项','待清理'):return
        g.keep=''; g.status='待选择保留项'; self.refresh()

    def run_task(self,fn):
        self.busy=True
        for button in (self.keep_button,self.reset_button,self.clean_button):button.configure(state='disabled')
        def worker():
            try:self.events.put(('done',fn()))
            except Exception as exc:self.events.put(('error',str(exc)))
        threading.Thread(target=worker,daemon=False).start()

    def clean(self):
        if self.busy:return
        selected=[g for g in self.groups if g.keep and g.status=='待清理']
        count=sum(len(g.members)-1 for g in selected)
        if not count:return
        if not messagebox.askyesno('确认同名清理',f'按你指定的保留项，清理 {len(selected)} 组中的其余 {count} 个文件。\n同名文件可能是不同版本，这些文件将移入回收站。是否继续？',parent=self):return
        self.run_task(lambda:('clean',clean_name_groups(selected,recycle_file)))

    def poll(self):
        try:kind,value=self.events.get_nowait()
        except queue.Empty:self.after(100,self.poll);return
        self.busy=False; self.reset_button.configure(state='normal')
        if kind=='error':
            self.refresh(); self.notes.insert('end','\n'+value)
        else:
            self.refresh(); self.notes.insert('end',f'\n本次已移入回收站 {value[1]} 个文件。')
            self.master.clear_results()
        self.after(100,self.poll)

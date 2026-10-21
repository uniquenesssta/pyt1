"""重复字体扫描、勾选预览和回收站清理窗口。"""
import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from ..core.duplicates import scan_duplicates, clean_duplicates
from ..storage.recycle import recycle_file


class DuplicateWindow(tk.Toplevel):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.title('重复字体清理')
        self.geometry('1080x620')
        self.minsize(780, 420)
        self.transient(parent)
        self.grab_set()
        self.config_data = config
        self.items = []
        self.checked = set()
        self.busy = False
        self.events = queue.Queue()
        self.protocol('WM_DELETE_WINDOW', self.close)
        bar = ttk.Frame(self, padding=10)
        bar.pack(fill='x')
        self.scan = ttk.Button(bar, text='扫描重复字体', command=self.start_scan)
        self.scan.pack(side='left')
        self.clean = ttk.Button(bar, text='移入回收站', command=self.start_clean, state='disabled')
        self.clean.pack(side='left', padx=8)
        ttk.Button(bar, text='全选 / 取消全选', command=self.toggle_all).pack(side='left')
        ttk.Button(bar, text="同名字体对比", command=self.open_same_names).pack(side="left", padx=8)
        self.summary = tk.StringVar(value='按完整文件内容判断；每组按路径排序保留第一份。')
        ttk.Label(self, textvariable=self.summary, padding=10).pack(fill='x')
        frame = ttk.Frame(self, padding=(10, 0))
        frame.pack(fill='both', expand=True)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(frame, columns=('check','status','path','keep','reason'), show='headings')
        for name, label, width in [('check','清理',55),('status','状态',110),('path','重复文件（移入回收站）',360),('keep','保留文件',360),('reason','说明',260)]:
            self.tree.heading(name, text=label)
            self.tree.column(name, width=width, stretch=False)
        self.tree.grid(row=0,column=0,sticky='nsew')
        y = ttk.Scrollbar(frame, orient='vertical', command=self.tree.yview)
        x = ttk.Scrollbar(frame, orient='horizontal', command=self.tree.xview)
        y.grid(row=0,column=1,sticky='ns'); x.grid(row=1,column=0,sticky='ew')
        self.tree.configure(yscrollcommand=y.set,xscrollcommand=x.set)
        self.tree.bind('<Button-1>',self.toggle)
        self.details = tk.Text(self, height=5, wrap='word')
        self.details.pack(fill='x', padx=10,pady=10)
        self.after(100,self.poll)
        self.start_scan()

    def open_same_names(self):
        if self.busy: return
        from .name_comparison import NameComparisonWindow
        NameComparisonWindow(self, self.config_data)

    def close(self):
        if self.busy:
            messagebox.showinfo('正在处理','请等待任务完成后关闭。',parent=self)
            return
        self.destroy()

    def render(self):
        self.tree.delete(*self.tree.get_children())
        for i, item in enumerate(self.items):
            self.tree.insert('', 'end', iid=str(i), values=('☑' if i in self.checked else '☐',item.status,item.path,item.keep,item.reason))
        self.clean.configure(state='normal' if self.checked and not self.busy else 'disabled')
        self.summary.set(f'重复文件 {len(self.items)} 项，已勾选 {len(self.checked)} 项；每组保留文件不会清理。')

    def toggle(self,event):
        if self.busy or self.tree.identify_column(event.x) != '#1': return
        row = self.tree.identify_row(event.y)
        if not row: return
        i = int(row)
        if self.items[i].status != '待清理': return
        if i in self.checked: self.checked.remove(i)
        else: self.checked.add(i)
        self.render()

    def toggle_all(self):
        if self.busy: return
        available = {i for i,p in enumerate(self.items) if p.status == '待清理'}
        self.checked = set() if self.checked == available else available
        self.render()

    def run_task(self, function):
        self.busy = True
        self.scan.configure(state='disabled')
        self.clean.configure(state='disabled')
        def worker():
            try: self.events.put(('done',function()))
            except Exception as exc: self.events.put(('error',str(exc)))
        threading.Thread(target=worker,daemon=False).start()

    def start_scan(self):
        if self.busy: return
        self.items = []; self.checked = set(); self.render()
        self.summary.set('正在扫描并校验文件内容…')
        c = self.config_data
        self.run_task(lambda: ('scan',scan_duplicates(c['folder'],c['extensions'],c['recursive'])))

    def start_clean(self):
        if self.busy or not self.checked: return
        selected = [self.items[i] for i in sorted(self.checked)]
        if not messagebox.askyesno('确认清理', f'将勾选的 {len(selected)} 个重复字体文件移入回收站。\n每组保留文件不动。是否继续？',parent=self): return
        self.summary.set('正在重新校验并移入回收站…')
        self.run_task(lambda: ('clean',clean_duplicates(selected,recycle_file)))

    def poll(self):
        try:
            kind, value = self.events.get_nowait()
        except queue.Empty:
            self.after(100,self.poll)
            return
        self.busy = False
        self.scan.configure(state='normal')
        if kind == 'error':
            self.details.insert('end',value+'\n')
        elif value[0] == 'scan':
            self.items, errors = value[1]
            self.checked = set(range(len(self.items)))
            self.details.delete('1.0','end')
            self.details.insert('end','\n'.join(errors) if errors else '扫描完成。点击第一列可取消不想清理的文件。')
        else:
            self.checked = {i for i in self.checked if self.items[i].status == '待清理'}
            self.details.insert('end',f'\n已移入回收站 {value[1]} 项。失败原因见说明列。')
            # 清理后废弃主窗口旧改名计划，避免引用已经移走的文件。
            self.master.clear_results()
        self.render()
        self.after(100,self.poll)

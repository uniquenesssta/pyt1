"""同名字体对比窗口布局。"""
import tkinter as tk
from tkinter import ttk


class NameComparisonLayout:
    def build(self):
        toolbar = ttk.Frame(self,padding=10); toolbar.pack(fill='x')
        self.keep_button = ttk.Button(toolbar,text='保留选中的这一份',command=self.choose_keep,state='disabled')
        self.keep_button.pack(side='left',padx=8)
        self.reset_button = ttk.Button(toolbar,text='取消本组清理',command=self.reset_group)
        self.reset_button.pack(side='left')
        self.clean_button = ttk.Button(toolbar,text='清理已确认组的其余文件',command=self.clean,state='disabled')
        self.clean_button.pack(side='left',padx=8)
        self.summary = tk.StringVar(value='正在扫描同名字体…')
        ttk.Label(self,textvariable=self.summary,padding=10).pack(fill='x')
        panel = ttk.Panedwindow(self,orient='horizontal'); panel.pack(fill='both',expand=True,padx=10)
        left = ttk.Frame(panel); right = ttk.Frame(panel); panel.add(left,weight=1); panel.add(right,weight=4)
        self.groups_list = tk.Listbox(left,width=30,exportselection=False)
        self.groups_list.pack(side='left',fill='both',expand=True)
        scroll = ttk.Scrollbar(left,command=self.groups_list.yview); scroll.pack(side='right',fill='y')
        self.groups_list.configure(yscrollcommand=scroll.set)
        self.groups_list.bind('<<ListboxSelect>>',self.show_group)
        columns = ('choice','file','name','style','version','size','glyphs','characters','hash','path')
        self.table = ttk.Treeview(right,columns=columns,show='headings',selectmode='browse')
        for key,label,width in zip(columns,('处理','文件名','内部完整名称','样式','版本','字节数','字形数','字符数','SHA-256','完整路径'),(90,220,220,100,180,100,80,80,460,450)):
            self.table.heading(key,text=label); self.table.column(key,width=width,stretch=False)
        right.rowconfigure(0,weight=1); right.columnconfigure(0,weight=1)
        self.table.grid(row=0,column=0,sticky='nsew')
        y=ttk.Scrollbar(right,orient='vertical',command=self.table.yview); y.grid(row=0,column=1,sticky='ns')
        x=ttk.Scrollbar(right,orient='horizontal',command=self.table.xview); x.grid(row=1,column=0,sticky='ew')
        self.table.configure(yscrollcommand=y.set,xscrollcommand=x.set)
        self.notes = tk.Text(self,height=7,wrap='word'); self.notes.pack(fill='x',padx=10,pady=10)

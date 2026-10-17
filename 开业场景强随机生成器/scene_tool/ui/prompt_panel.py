from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from scene_tool.config.defaults import DEFAULT_CONSTRAINTS

def build_prompt_panel(self, body):
    right = ttk.Frame(body)
    right.grid(row=0, column=1, sticky='nsew')
    tabs = ttk.Notebook(right)
    tabs.pack(fill='both', expand=True)
    prompt_tab, rules_tab = ttk.Frame(tabs), ttk.Frame(tabs)
    tabs.add(prompt_tab, text='  完整提示词  ')
    tabs.add(rules_tab, text='  固定要求 / 补充  ')
    self.prompt = ScrolledText(prompt_tab, wrap='word', undo=True, font=('Microsoft YaHei UI', 11), padx=14, pady=14, relief='flat', width=35, height=15)
    self.prompt.pack(fill='both', expand=True, pady=(8, 0))
    ttk.Label(rules_tab, text='固定要求（默认保留原图紫色背景和3.5×2.2米大板）').pack(anchor='w', pady=10)
    self.constraints = ScrolledText(rules_tab, wrap='word', font=('Microsoft YaHei UI', 10), height=14, width=35, undo=True)
    self.constraints.pack(fill='both', expand=True)
    self.constraints.insert('1.0', DEFAULT_CONSTRAINTS)
    ttk.Label(rules_tab, text='补充要求').pack(anchor='w', pady=10)
    self.extra = ScrolledText(rules_tab, wrap='word', font=('Microsoft YaHei UI', 10), height=5, width=35, undo=True)
    self.extra.pack(fill='both', expand=True)
    for widget in (self.constraints, self.extra):
        widget.bind('<KeyRelease>', self.schedule_refresh)
    actions = ttk.Frame(right, padding=(0, 12, 0, 0))
    actions.pack(fill='x')
    ttk.Button(actions, text='复制提示词', style='Primary.TButton', command=self.copy_prompt).pack(side='left')
    ttk.Button(actions, text='更新提示词', command=lambda: self.refresh(force=True)).pack(side='left', padx=8)
    ttk.Button(actions, text='导出 TXT', command=self.export).pack(side='left')

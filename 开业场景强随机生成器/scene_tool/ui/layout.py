from tkinter import ttk
from scene_tool.ui.parameter_panel import build_parameters
from scene_tool.ui.prompt_panel import build_prompt_panel

def build_ui(self):
    header = ttk.Frame(self, padding=(24, 18))
    header.pack(fill='x')
    ttk.Label(header, text='开业场景 · 12维强随机', font=('Microsoft YaHei UI', 21, 'bold')).pack(anchor='w')
    ttk.Label(header, text='独立抽取每一维，让场景真正换一种样子。抽取 → 编辑 → 复制提示词').pack(anchor='w', pady=(5, 0))
    body = ttk.Frame(self, padding=(24, 0, 24, 12))
    body.pack(fill='both', expand=True)
    body.columnconfigure(0, weight=1, uniform='cols')
    body.columnconfigure(1, weight=1, uniform='cols')
    body.rowconfigure(0, weight=1)
    build_parameters(self, body)
    build_prompt_panel(self, body)
    ttk.Label(self, textvariable=self.status, padding=(24, 8), wraplength=1100).pack(fill='x')

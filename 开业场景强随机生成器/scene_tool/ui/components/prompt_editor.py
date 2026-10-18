"""Prompt reader/editor with an inline collapsible supplement."""
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText


def prompt_editor(parent):
    header = ttk.Frame(parent)
    header.pack(fill='x', pady=(0, 8))
    ttk.Label(header, text='完整提示词', style='Section.TLabel').pack(side='left')
    prompt = ScrolledText(parent, wrap='word', undo=True, width=35, height=12,
                          font=('Microsoft YaHei UI', 11), relief='flat', padx=12, pady=12)
    prompt.pack(fill='both', expand=True)
    extra_box = ttk.Frame(parent)
    extra = ScrolledText(extra_box, wrap='word', undo=True, width=35, height=4,
                         font=('Microsoft YaHei UI', 10), relief='flat', padx=8, pady=8)
    extra.pack(fill='x')
    toggle = ttk.Button(parent, text='展开补充要求')
    toggle.pack(fill='x', pady=(8, 0))
    def expand():
        if extra_box.winfo_manager():
            extra_box.pack_forget()
            toggle.configure(text='展开补充要求')
        else:
            extra_box.pack(fill='x', after=toggle, pady=(6, 0))
            toggle.configure(text='收起补充要求')
    toggle.configure(command=expand)
    return prompt, extra, header

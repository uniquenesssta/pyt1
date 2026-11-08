"""A compact picker with the real prompt, direct copy, and explicit application."""
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText


def show_variants(parent, variants, apply):
    dialog = tk.Toplevel(parent)
    dialog.title('4套方案 · 预览与选择')
    dialog.geometry('980x660')
    dialog.minsize(720, 480)
    dialog.transient(parent.winfo_toplevel())
    dialog.grab_set()
    body = ttk.Frame(dialog, padding=16)
    body.pack(fill='both',expand=True)
    note = '保留当前产品、材质、画幅和锁定项；选中查看完整提示词。'
    if len(variants) < 4:
        note = f'本轮找到{len(variants)}套不同方案；可解锁机位或构图后重试。'
    note_label = ttk.Label(body,text=note,wraplength=900)
    note_label.pack(anchor='w',pady=(0,12))
    choices = ttk.Frame(body)
    choices.pack(fill='x')
    selected = tk.IntVar(value=0)
    summary = tk.StringVar()
    summary_label = ttk.Label(body,textvariable=summary,wraplength=900)
    summary_label.pack(fill='x',pady=10)
    def resize(event):
        for label in (note_label, summary_label):
            label.configure(wraplength=max(300, event.width - 32))
    body.bind('<Configure>',resize)
    preview = ScrolledText(body,wrap='word',font=('Microsoft YaHei UI',11))
    preview.pack(fill='both',expand=True)
    def change():
        item = variants[selected.get()]
        main = ('镜头类别','机位','构图','空间','摆位','光线','反光')
        summary.set('\n'.join(f'{key}：{item.features[key]}' for key in main if key in item.features))
        preview.configure(state='normal')
        preview.delete('1.0','end')
        preview.insert('1.0',item.prompt)
        preview.configure(state='disabled')
    for index in range(len(variants)):
        ttk.Radiobutton(choices,text=f'方案 {index+1}',variable=selected,value=index,command=change).pack(side='left',padx=(0,24))
    footer = ttk.Frame(body)
    footer.pack(fill='x',pady=(12,0))
    status = tk.StringVar()
    ttk.Label(footer,textvariable=status).pack(side='left')
    def copy():
        dialog.clipboard_clear()
        dialog.clipboard_append(variants[selected.get()].prompt)
        status.set('已复制所选方案')
    def commit():
        if apply(variants[selected.get()]):
            dialog.destroy()
    ttk.Button(footer,text='复制所选提示词',style='Primary.TButton',command=copy).pack(side='right')
    ttk.Button(footer,text='应用到主界面',command=commit).pack(side='right',padx=8)
    ttk.Button(footer,text='关闭',command=dialog.destroy).pack(side='right')
    change()

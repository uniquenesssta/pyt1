"""批量删除确认：完整路径列表可滚动查看。"""
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText


def confirm_delete(parent, paths):
    dialog = tk.Toplevel(parent)
    dialog.title('确认删除文件')
    dialog.geometry('760x420')
    dialog.transient(parent)
    dialog.grab_set()
    result = False
    ttk.Label(dialog, text=f'将选中的 {len(paths)} 个文件移入回收站：', padding=10).pack(anchor='w')
    listing = ScrolledText(dialog, wrap='none', height=15)
    listing.pack(fill='both', expand=True, padx=10)
    listing.insert('1.0', '\n'.join(paths))
    listing.configure(state='disabled')
    horizontal = ttk.Scrollbar(dialog, orient='horizontal', command=listing.xview)
    horizontal.pack(fill='x', padx=10)
    listing.configure(xscrollcommand=horizontal.set)
    buttons = ttk.Frame(dialog, padding=10)
    buttons.pack(fill='x')
    def accept():
        nonlocal result
        result = True
        dialog.destroy()
    cancel = ttk.Button(buttons, text='取消', command=dialog.destroy)
    cancel.pack(side='right')
    ttk.Button(buttons, text='确认移入回收站', command=accept).pack(side='right', padx=8)
    dialog.bind('<Escape>', lambda _event: dialog.destroy())
    dialog.protocol('WM_DELETE_WINDOW', dialog.destroy)
    cancel.focus_set()
    parent.wait_window(dialog)
    return result

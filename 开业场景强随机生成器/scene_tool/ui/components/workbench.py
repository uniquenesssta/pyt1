"""Common adjustable columns and fixed primary actions."""
import tkinter as tk
from tkinter import ttk


def workbench(parent):
    footer = ttk.Frame(parent, padding=(0, 12, 0, 0))
    footer.pack(side='bottom', fill='x')
    panes = tk.PanedWindow(parent, orient='horizontal', sashwidth=8, sashrelief='flat',
                          opaqueresize=False, borderwidth=0, bg='#e2e5ec', showhandle=False)
    panes.pack(fill='both', expand=True)
    left, right = ttk.Frame(panes), ttk.Frame(panes, padding=(12, 0, 0, 0))
    panes.add(left, minsize=320, width=500, stretch='always')
    panes.add(right, minsize=350, stretch='always')
    return left, right, footer


def actions(footer, randomize, copy, unlock, update, export, reset, undo):
    ttk.Button(footer, text='重新随机', style='Primary.TButton', command=randomize).pack(side='left')
    ttk.Button(footer, text='全部解锁', command=unlock).pack(side='left', padx=8)
    ttk.Button(footer, text='复制提示词', style='Primary.TButton', command=copy).pack(side='right')
    more = ttk.Menubutton(footer, text='更多操作')
    menu = tk.Menu(more, tearoff=False)
    for label, callback in [('更新提示词', update), ('导出 TXT', export),
                            ('复原默认提示词', reset), ('撤销复原', undo)]:
        menu.add_command(label=label, command=callback)
    more.configure(menu=menu)
    more.pack(side='right', padx=8)
    return menu


class MenuAction:
    """Expose an action state to controllers independently of its placement."""
    def __init__(self, menu, index):
        self.menu, self.index = menu, index

    def configure(self, **options):
        self.menu.entryconfigure(self.index, **options)

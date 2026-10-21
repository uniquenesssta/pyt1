"""保留 Windows 原生控件，仅统一文字尺寸与可读性。"""
from tkinter import ttk, font

COLORS = {
    'background': '#f0f0f0', 'surface': '#ffffff', 'text': '#202020',
    'muted': '#606060', 'border': '#d8d8d8', 'accent': '#3478c5',
    'tint': '#f4f4f4', 'hot': '#b42318', 'cold': '#175cd3',
}


def apply_theme(root):
    style = ttk.Style(root)
    # Retain platform controls, including their button borders and selected tabs.
    style.theme_use('vista' if 'vista' in style.theme_names() else 'default')
    families = set(font.families(root))
    default_font = font.nametofont('TkDefaultFont')
    family = 'Microsoft YaHei UI' if 'Microsoft YaHei UI' in families else default_font.actual('family')
    default_font.configure(family=family, size=10)
    face = (family, 10)
    root.option_add('*Font', face)
    style.configure('.', font=face)
    background = style.lookup('TFrame', 'background') or root.cget('background')
    root.configure(background=background)
    style.configure('Workspace.TFrame', background=background)
    style.configure('Workspace.TLabel', background=background, foreground=COLORS['muted'])
    style.configure('Muted.TLabel', foreground=COLORS['muted'])
    style.configure('Title.TLabel', font=(family, 12, 'bold'), background=background)
    style.configure('Section.TLabel', font=(family, 11, 'bold'))
    style.configure('TButton', padding=(8, 3))
    style.configure('Primary.TButton', font=(family, 10, 'bold'), padding=(10, 3))
    style.configure('TEntry', padding=3)
    style.configure('TCombobox', padding=3)
    style.configure('TNotebook.Tab', padding=(10, 4))
    style.map('TNotebook.Tab', padding=[('selected', (10, 4)), ('!selected', (10, 4))])
    style.configure('Treeview', rowheight=max(26, default_font.metrics('linespace') + 8), font=face)
    style.configure('Treeview.Heading', font=(family, 10, 'bold'), padding=(4, 3))
    return style

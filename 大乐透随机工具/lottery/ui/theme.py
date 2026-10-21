"""桌面视觉规范：颜色、字号与间距统一在这里维护。"""
from tkinter import ttk, font

COLORS = {
    'background': '#f4f6fa', 'surface': '#ffffff', 'text': '#172b4d',
    'muted': '#596b84', 'border': '#dce3ed', 'accent': '#255ac4',
    'tint': '#edf3ff', 'hot': '#b42318', 'cold': '#175cd3',
}


def apply_theme(root):
    families = set(font.families(root))
    family = next((name for name in ('Microsoft YaHei UI', 'Noto Sans CJK SC', 'Noto Sans SC')
                   if name in families), font.nametofont('TkDefaultFont').actual('family'))
    font.nametofont('TkDefaultFont').configure(size=10)
    face = (family, 10)
    root.option_add('*Font', face)
    root.configure(background=COLORS['background'])
    style = ttk.Style(root)
    # clam allows consistent colors on Windows as well as Linux.
    style.theme_use('clam')
    style.configure('.', font=face, background=COLORS['surface'], foreground=COLORS['text'])
    style.configure('TFrame', background=COLORS['surface'])
    style.configure('Workspace.TFrame', background=COLORS['background'])
    style.configure('TLabel', padding=0)
    style.configure('Muted.TLabel', foreground=COLORS['muted'])
    style.configure('Workspace.TLabel', background=COLORS['background'], foreground=COLORS['muted'])
    style.configure('Title.TLabel', font=(family, 16, 'bold'), background=COLORS['background'])
    style.configure('Section.TLabel', font=(family, 12, 'bold'))
    style.configure('TButton', padding=(12, 7), borderwidth=1, relief='flat',
                    bordercolor=COLORS['border'], focusthickness=1, focuscolor=COLORS['accent'])
    style.map('TButton', background=[('active', COLORS['tint'])],
              foreground=[('disabled', COLORS['muted'])])
    style.configure('Primary.TButton', background=COLORS['accent'], foreground='white',
                    font=(family, 10, 'bold'), bordercolor=COLORS['accent'])
    style.map('Primary.TButton', background=[('disabled', '#d9e2f4'), ('active', '#17479f')],
              foreground=[('disabled', COLORS['muted']), ('!disabled', 'white')])
    style.configure('TEntry', padding=6, fieldbackground='white', bordercolor=COLORS['border'])
    style.configure('TCombobox', padding=5, arrowsize=14, bordercolor=COLORS['border'])
    style.map('TCombobox', fieldbackground=[('readonly', 'white')],
              selectbackground=[('readonly', COLORS['tint'])],
              selectforeground=[('readonly', COLORS['text'])])
    style.configure('TNotebook', background=COLORS['background'], borderwidth=0, tabmargins=(0, 0, 0, 8))
    style.configure('TNotebook.Tab', padding=(18, 9), background=COLORS['surface'], borderwidth=0)
    style.map('TNotebook.Tab', background=[('selected', COLORS['accent']), ('active', COLORS['tint'])],
              foreground=[('selected', 'white')])
    style.configure('Treeview', rowheight=32, font=face, background='white', fieldbackground='white',
                    borderwidth=0, lightcolor=COLORS['border'], darkcolor=COLORS['border'])
    style.configure('Treeview.Heading', font=(family, 10, 'bold'), padding=(8, 8),
                    background=COLORS['tint'], relief='flat', borderwidth=0)
    style.map('Treeview', background=[('selected', '#dce8ff')], foreground=[('selected', '#12346c')])
    style.configure('TLabelframe', bordercolor=COLORS['border'], relief='solid')
    style.configure('TLabelframe.Label', foreground=COLORS['muted'])
    style.configure('TPanedwindow', background=COLORS['background'], sashwidth=8)
    return style

import sys
from tkinter import ttk

def apply_theme(self):
    self.configure(bg='#f3f5fa')
    style = ttk.Style(self)
    native = sys.platform == 'win32' and 'vista' in style.theme_names()
    style.theme_use('vista' if native else 'clam')
    style.configure('.', font=('Microsoft YaHei UI', 10))
    style.configure('TFrame', background='#f3f5fa')
    style.configure('TLabel', background='#f3f5fa', foreground='#24324b')
    style.configure('TCheckbutton', background='#f3f5fa')
    style.configure('TButton', padding=(12, 7))
    if native:
        style.element_create('Accent.border', 'from', 'clam', 'Button.border')
        style.layout('Primary.TButton', [('Accent.border', {'sticky': 'nswe', 'children': [
            ('Button.padding', {'sticky': 'nswe', 'children': [
                ('Button.label', {'sticky': 'nswe'})]})]})])
    style.configure('Primary.TButton', background='#6357df', foreground='white')
    style.map('Primary.TButton', background=[('active', '#5043c5')])

    style.configure('Section.TLabel', font=('Microsoft YaHei UI', 11, 'bold'), foreground='#24324b')
    style.configure('Result.TFrame', background='#ffffff')
    style.configure('Result.TLabel', background='#ffffff', foreground='#253148', font=('Microsoft YaHei UI', 10))
    style.configure('Muted.TLabel', background='#ffffff', foreground='#747d8c', font=('Microsoft YaHei UI', 9))
    style.configure('Result.TCheckbutton', background='#ffffff')
    style.layout('Result.TCheckbutton', [('Checkbutton.padding', {'sticky': 'nswe', 'children': [
        ('Checkbutton.focus', {'sticky': 'nswe', 'children': [
            ('Checkbutton.indicator', {'sticky': 'nswe'})]})]})])


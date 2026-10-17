from tkinter import ttk

def apply_theme(self):
    self.configure(bg='#f3f5fa')
    style = ttk.Style(self)
    style.theme_use('clam')
    style.configure('.', font=('Microsoft YaHei UI', 10))
    style.configure('TFrame', background='#f3f5fa')
    style.configure('TLabel', background='#f3f5fa', foreground='#24324b')
    style.configure('TCheckbutton', background='#f3f5fa')
    style.configure('TButton', padding=(12, 7))
    style.configure('Primary.TButton', background='#6357df', foreground='white')
    style.map('Primary.TButton', background=[('active', '#5043c5')])

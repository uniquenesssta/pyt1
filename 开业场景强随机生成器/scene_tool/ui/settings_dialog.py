"""Low-frequency opening-scene settings, outside the random workflow."""
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from scene_tool.config.defaults import INDUSTRIES


def open_settings(view):
    dialog = tk.Toplevel(view)
    dialog.title('开业场景设置')
    dialog.geometry('640x540')
    dialog.transient(view)
    dialog.grab_set()
    body = ttk.Frame(dialog, padding=18)
    body.pack(fill='both', expand=True)
    industry = tk.StringVar(value=view.industry.get())
    flags = [(label, variable, tk.BooleanVar(value=variable.get())) for label, variable in (
        ('强随机轮换', view.strong), ('随机开业文案', view.copy_random),
        ('品牌和街道随机组合', view.generated_names))]
    ttk.Label(body, text='行业（仅影响开业提示词）').pack(anchor='w')
    ttk.Combobox(body, textvariable=industry, values=INDUSTRIES).pack(fill='x', pady=8)
    for label, _, temporary in flags:
        ttk.Checkbutton(body, text=label, variable=temporary).pack(anchor='w', pady=3)
    ttk.Label(body, text='固定要求').pack(anchor='w', pady=(12, 6))
    editor = ScrolledText(body, wrap='word', height=10, undo=True)
    editor.pack(fill='both', expand=True)
    editor.insert('1.0', view.constraints.get('1.0', 'end-1c'))
    def save():
        view.industry.set(industry.get())
        for _, variable, temporary in flags:
            variable.set(temporary.get())
        view.constraints.delete('1.0', 'end')
        view.constraints.insert('1.0', editor.get('1.0', 'end-1c'))
        view.schedule_refresh()
        view.save()
        dialog.destroy()
    ttk.Button(body, text='保存设置', command=save).pack(pady=(12, 0))

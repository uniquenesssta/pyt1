"""Inline preset naming, selection, save and deletion beside material editing."""
import tkinter as tk
from tkinter import ttk, messagebox
from scene_tool.storage import material_presets as storage
from scene_tool.ui.material_binding import apply_material

def material_preset_row(results, view, scene=False):
    name=tk.StringVar()
    label=results.result('材质预设',name,None,choices=[])
    label.configure(width=10)
    row,box=label.master,label.editor
    def read():
        try: return storage.load()
        except (OSError,ValueError) as exc:
            messagebox.showwarning('读取材质预设失败',str(exc),parent=view)
            return None
    def refresh():
        data=read()
        if data is not None: box.configure(values=list(data))
        return data
    def choose(_=None):
        data=read()
        if data is not None and name.get() in data:
            if not apply_material(view,data[name.get()],scene): name.set('')
    def save():
        data=read()
        if data is None: return
        key=name.get().strip()
        value=(view.close_material if scene else view.values['close_material']).get()
        if key in data and data[key]!=value.strip() and not messagebox.askyesno('覆盖材质预设',f'更新“{key}”的材质描述？',parent=view): return
        try:
            storage.save(key,value)
            name.set(key)
            refresh()
        except (OSError,ValueError) as exc:
            messagebox.showwarning('保存失败',str(exc),parent=view)
    def delete():
        data=read()
        key=name.get()
        if data is None or key not in data: return
        if not messagebox.askyesno('删除材质预设',f'删除“{key}”？当前填写的材质会保留。',parent=view): return
        try:
            storage.delete(key)
            name.set('')
            refresh()
        except (OSError,ValueError) as exc:
            messagebox.showwarning('删除失败',str(exc),parent=view)
    box.configure(postcommand=refresh)
    box.bind('<<ComboboxSelected>>',choose)
    # Controls occupy the same row; description retains its own full-width entry.
    ttk.Button(row,text='保存',width=4,style='Inline.TButton',command=save).pack(side='left',padx=(2,0))
    ttk.Button(row,text='删除',width=4,style='Inline.TButton',command=delete).pack(side='left',padx=2)
    from scene_tool.ui.components.tooltip import Tooltip
    Tooltip(box,lambda:'输入名称后保存上方材质描述；下拉选择已有预设直接调用。')
    refresh()
    return row

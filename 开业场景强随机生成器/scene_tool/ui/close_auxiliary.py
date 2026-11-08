"""Edit the existing secondary values, locks and visibility in a small modal."""
import tkinter as tk
from tkinter import ttk, messagebox
from scene_tool.config.closeup import CLOSEUP
from scene_tool.config.close_auxiliary import GROUPS
from scene_tool.ui.components.results import ResultList


def open_auxiliary(view, scene=False):
    style=view.model.render_style if scene else view.render_style.get()
    if style!=CLOSEUP:
        messagebox.showinfo('近景辅助项','切换到近景摄影后可调整。',parent=view)
        return
    if scene:
        mapping={d.get('close_key',d['key']):d['key'] for d in view.model.active_profile()['dimensions']}
        pools=view.model.active_pools()
        labels={d['key']:d['label'] for d in view.model.active_profile()['dimensions']}
    else:
        from scene_tool.config.close_dimensions import LABELS
        mapping={k:k for _,keys in GROUPS for k in keys}
        pools=view.engine.scoped_pools(view.industry.get(),view.values['environment'].get(),CLOSEUP)
        labels=LABELS
    dialog=tk.Toplevel(view)
    dialog.title('近景辅助项')
    dialog.geometry('820x360')
    dialog.minsize(660,320)
    dialog.transient(view.winfo_toplevel())
    dialog.grab_set()
    ttk.Label(dialog,text='保留原有取值、锁定和隐藏。修改后保存才生效。',padding=12).pack(anchor='w')
    body=ttk.Frame(dialog,padding=(12,0,12,12))
    body.pack(fill='both',expand=True)
    results=ResultList(body)
    temporary={}
    for title,keys in GROUPS:
        results.group(title)
        for canonical in keys:
            key=mapping[canonical]
            v=tk.StringVar(value=view.values[key].get())
            lock=tk.BooleanVar(value=view.locks[key].get())
            hide=tk.BooleanVar(value=view.hidden[key].get())
            temporary[key]=(v,lock,hide)
            results.result(labels[key],v,lock,choices=pools[key],hidden=hide)
    def save():
        if any(not v.get().strip() and not hide.get() for v,_,hide in temporary.values()):
            messagebox.showwarning('未填完整','未隐藏的项目需要填写内容。',parent=dialog)
            return
        if scene:
            if not view.allow_replace(): return
            view.updating=True
        else:
            if view.edited() and not messagebox.askyesno('更新提示词','保存将替换右侧手改提示词，继续吗？',parent=dialog): return
            if view.pending:
                view.after_cancel(view.pending)
                view.pending=None
            view.ready=False
        before={key:(view.values[key].get(),view.locks[key].get(),view.hidden[key].get()) for key in temporary}
        for key,(v,lock,hide) in temporary.items():
            view.values[key].set(v.get().strip())
            view.locks[key].set(lock.get())
            view.hidden[key].set(hide.get())
        try:
            if scene:
                view.capture()
                content=view.model.generate()
            else:
                content=view.generated()
        except ValueError as exc:
            for key,(value,lock,hide) in before.items():
                view.values[key].set(value)
                view.locks[key].set(lock)
                view.hidden[key].set(hide)
            if scene: view.capture()
            messagebox.showwarning('未保存',str(exc),parent=dialog)
            return
        finally:
            if scene: view.updating=False
            else: view.ready=True
        if scene:
            view.model.prompt=view.model.rendered=content
            view.model.undo=None
            view.show_prompt()
            view.persist()
        else:
            view.set_prompt(content)
            view.prompt_reset.snapshot=None
            view.undo_reset_button.configure(state='disabled')
            view.save()
        dialog.destroy()
    footer=ttk.Frame(dialog,padding=12)
    footer.pack(fill='x')
    ttk.Button(footer,text='保存',style='Primary.TButton',command=save).pack(side='right')
    ttk.Button(footer,text='取消',command=dialog.destroy).pack(side='right',padx=8)

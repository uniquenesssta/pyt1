"""Apply material text through the same prompt/state path as other editable values."""
from tkinter import messagebox

def apply_material(view, description, scene=False):
    variable = view.close_material if scene else view.values['close_material']
    before = variable.get()
    if scene:
        if not view.allow_replace(): return False
        view.updating=True
    else:
        if view.edited() and not messagebox.askyesno('调用材质预设','更新材质并替换手改提示词？',parent=view):
            return False
        if view.pending:
            view.after_cancel(view.pending)
            view.pending=None
        view.ready=False
    try:
        variable.set(description)
        if scene:
            view.capture()
            content=view.model.generate()
        else:
            content=view.generated()
    except ValueError as exc:
        variable.set(before)
        if scene: view.capture()
        messagebox.showwarning('无法调用',str(exc),parent=view)
        return False
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
    return True


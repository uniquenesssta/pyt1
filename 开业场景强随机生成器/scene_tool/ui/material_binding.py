"""Apply material description and finish atomically, preserving conflicting locks."""
from tkinter import messagebox
from scene_tool.config import material_finish as finish_config
from scene_tool.domain.material_finish import reconcile


def finish_variable(view,scene=False):
    return getattr(view,'close_finish',None) if scene else view.values.get(finish_config.KEY)


def apply_material(view,description,scene=False,finish=None):
    variable=view.close_material if scene else view.values['close_material']
    surface=finish_variable(view,scene)
    before_text=variable.get()
    old_finish=surface.get() if surface else (view.model.close_finish if scene else finish_config.FOLLOW)
    if scene:
        if not view.allow_replace(): return False
        values=dict(view.model.values)
        locks={k for k,v in view.model.locks.items() if v}
        light_key=next(d['key'] for d in view.model.active_profile()['dimensions'] if d.get('close_key')=='detail_light')
    else:
        if view.edited() and not messagebox.askyesno('更新材质','更新材质并替换手改提示词？',parent=view): return False
        values=view.current()
        locks={k for k,v in view.locks.items() if v.get()}
        light_key='detail_light'
    try:
        new_finish=finish_config.normalize(old_finish if finish is None else finish)
        updated=reconcile(values,locks,new_finish,light_key)
    except ValueError as exc:
        messagebox.showwarning('材质设置未改变',str(exc),parent=view)
        return False
    if getattr(view,'pending',None):
        view.after_cancel(view.pending)
        view.pending=None
    if scene: view.updating=True
    else: view.ready=False
    try:
        variable.set(description)
        if surface: surface.set(new_finish)
        for key in ('detail_reflection',light_key):
            if key in getattr(view,'values',{}): view.values[key].set(updated[key])
        if scene:
            view.capture()
            view.model.values.update({k:updated[k] for k in ('detail_reflection',light_key)})
            view.model.close_finish=new_finish
            content=view.model.generate()
        else:
            content=view.generated()
    except ValueError as exc:
        variable.set(before_text)
        if surface: surface.set(old_finish)
        for key in ('detail_reflection',light_key):
            if key in getattr(view,'values',{}): view.values[key].set(values[key])
        if scene:
            view.capture()
            view.model.values=values
            view.model.close_finish=old_finish
        messagebox.showwarning('无法调用',str(exc),parent=view)
        return False
    finally:
        if scene: view.updating=False
        else: view.ready=True
    view.material_finish_value=new_finish
    if hasattr(view,'studio_values'):
        view.studio_values.update({k:updated[k] for k in ('detail_reflection',light_key)})
    from scene_tool.ui.material_finish import refresh_finish_choices
    refresh_finish_choices(view,scene)
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

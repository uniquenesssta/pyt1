"""Inline, explicit material finish selection, separate from light placement."""
from scene_tool.config import material_finish as config, surface_reflection as reflection, highlight_position as light
from scene_tool.ui.material_binding import apply_material, finish_variable
from scene_tool.domain.material_finish import compatible


def refresh_finish_choices(view,scene=False):
    if not hasattr(view,'combos'): return
    variable=finish_variable(view,scene)
    finish=variable.get() if variable else config.FOLLOW
    if scene:
        pools=view.model.active_pools()
        light_key=next(d['key'] for d in view.model.active_profile()['dimensions'] if d.get('close_key')==light.KEY)
    else:
        environment=view.values.get('environment')
        pools=view.engine.scoped_pools(view.industry.get(),environment.get() if environment else None,'近景摄影')
        light_key=light.KEY
    if reflection.KEY in view.combos:
        view.combos[reflection.KEY].configure(values=[s for s in pools[reflection.KEY] if compatible(finish,s)])
    if light_key in view.combos:
        positions=pools[light_key]
        if finish==config.MATTE: positions=[p for p in positions if p==light.NONE]
        elif finish!=config.FOLLOW: positions=[p for p in positions if p in light.OPTIONS and p!=light.NONE]
        view.combos[light_key].configure(values=positions)


def material_finish_row(results,view,scene=False):
    variable=finish_variable(view,scene)
    view.material_finish_value=variable.get()
    label=results.result('材质表面',variable,None,choices=config.OPTIONS,readonly=True,
        hint='明确材质的表面光泽；不根据名称猜测。选择后约束反光，灯位在兼容范围内随机。')
    def choose(_=None):
        selected=variable.get()
        previous=view.material_finish_value
        variable.set(previous)
        text=(view.close_material if scene else view.values['close_material']).get()
        apply_material(view,text,scene,finish=selected)
    label.editor.bind('<<ComboboxSelected>>',choose)
    return label.master

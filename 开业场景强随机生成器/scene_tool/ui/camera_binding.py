"""Keep visible camera candidates aligned with the active photographing mode."""
from scene_tool.domain.camera_modes import camera_pool


def sync_opening_camera(view):
    pool = camera_pool(view.engine.pools['camera'], view.values['environment'].get(), view.render_style.get())
    view.combos['camera'].configure(values=pool)
    if view.values['camera'].get() not in pool:
        view.values['camera'].set(pool[0])


def sync_scene_camera(panel):
    style = panel.model.render_style
    if style == '近景摄影':
        panel.size_row.grid_remove()
        panel.subject_row.grid()
        panel.reflection_row.grid()
        panel.reflection_row.master.rowconfigure(panel.reflection_row_index, weight=1, uniform='results')
        panel.material_row.grid()
        panel.material_preset_row.grid()
        panel.material_finish_row.grid()
        panel.material_finish_row.master.rowconfigure(panel.material_finish_row_index, weight=1, uniform='results')
        panel.material_preset_row.master.rowconfigure(panel.material_preset_row_index, weight=1, uniform='results')
        panel.material_row.master.rowconfigure(panel.material_row.grid_info()['row'], weight=1, uniform='results')
    else:
        panel.subject_row.grid_remove()
        panel.reflection_row.grid_remove()
        panel.reflection_row.master.rowconfigure(panel.reflection_row_index, weight=0, uniform='')
        panel.material_row.master.rowconfigure(panel.material_row_index, weight=0, uniform='')
        panel.material_row.grid_remove()
        panel.material_preset_row.grid_remove()
        panel.material_finish_row.grid_remove()
        panel.material_finish_row.master.rowconfigure(panel.material_finish_row_index, weight=0, uniform='')
        panel.material_preset_row.master.rowconfigure(panel.material_preset_row_index, weight=0, uniform='')
        panel.size_row.grid()
    previous_style = getattr(panel, '_camera_style', style)
    changed = previous_style != style
    panel._camera_style = style
    titles = ('近景布置', '近景内容', '近景拍摄') if style == '近景摄影' else ('环境空间', '装置与人物', '拍摄')
    for label, title in zip(panel.group_labels, titles):
        label.configure(text=title)
    if style == '近景摄影':
        from scene_tool.ui.studio_binding import sync_scene_studio
        for dimension in panel.model.active_profile()['dimensions']:
            panel.parameter_labels[dimension['key']].configure(text=dimension['label'])
        sync_scene_studio(panel)
        return
    pools = panel.model.active_pools()
    for dimension in panel.model.active_profile()['dimensions']:
        key = dimension['key']
        panel.parameter_labels[key].configure(text=dimension['label'])
        panel.combos[key].configure(values=pools[key])
        if key != 'camera' and (changed or not panel.model.values[key]) and panel.model.values[key] not in pools[key]:
            panel.model.values[key] = panel.model.rng.choice(pools[key])
        panel.values[key].set(panel.model.values[key])
    pool = panel.model.camera_pool()
    panel.combos['camera'].configure(values=pool)
    if panel.model.values['camera'] not in pool:
        panel.model.values['camera'] = pool[0]
    panel.values['camera'].set(panel.model.values['camera'])

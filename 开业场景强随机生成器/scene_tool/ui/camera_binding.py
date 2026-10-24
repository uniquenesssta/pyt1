"""Keep visible camera candidates aligned with the active photographing mode."""
from scene_tool.domain.camera_modes import camera_pool


def sync_opening_camera(view):
    pool = camera_pool(view.engine.pools['camera'], view.values['environment'].get(), view.render_style.get())
    view.combos['camera'].configure(values=pool)
    if view.values['camera'].get() not in pool:
        view.values['camera'].set(pool[0])


def sync_scene_camera(panel):
    style = panel.model.render_style
    previous_style = getattr(panel, '_camera_style', style)
    changed = previous_style != style
    panel._camera_style = style
    pools = panel.model.active_pools()
    for dimension in panel.model.active_profile()['dimensions']:
        key = dimension['key']
        panel.parameter_labels[key].configure(text=dimension['label'])
        panel.combos[key].configure(values=pools[key])
        if key != 'camera' and (changed or style == '商业效果图') and panel.model.values[key] not in pools[key]:
            panel.model.values[key] = panel.model.rng.choice(pools[key])
        panel.values[key].set(panel.model.values[key])
    pool = panel.model.camera_pool()
    panel.combos['camera'].configure(values=pool)
    if panel.model.values['camera'] not in pool:
        panel.model.values['camera'] = pool[0]
    panel.values['camera'].set(panel.model.values['camera'])

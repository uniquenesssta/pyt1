"""Keep visible camera candidates aligned with the active photographing mode."""
from scene_tool.domain.camera_modes import camera_pool


def sync_opening_camera(view):
    pool = camera_pool(view.engine.pools['camera'], view.values['environment'].get(), view.render_style.get())
    view.combos['camera'].configure(values=pool)
    if view.values['camera'].get() not in pool:
        view.values['camera'].set(pool[0])


def sync_scene_camera(panel):
    pool = panel.model.camera_pool()
    panel.combos['camera'].configure(values=pool)
    if panel.model.values['camera'] not in pool:
        panel.model.values['camera'] = pool[0]
    panel.values['camera'].set(panel.model.values['camera'])

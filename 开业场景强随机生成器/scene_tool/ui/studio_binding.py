"""Show the selected setup's compatible choices without adding a toolbar step."""
from tkinter import messagebox
from scene_tool.config.closeup import ANGLES, CLOSEUP
from scene_tool.generation.studio_shots import ShotConflict


def sync_opening_studio(view, fixed_camera=False, fixed_key=None):
    current = view.current()
    locks = {k for k, var in view.locks.items() if var.get()}
    if fixed_camera:
        locks.add('camera')
    if fixed_key:
        locks.add(fixed_key)
    values, options = view.engine.studio_draw(current, locks, view.industry.get(), keep=True)
    for key, value in values.items():
        if view.values[key].get() != value:
            view.values[key].set(value)
        view.combos[key].configure(values=ANGLES if key == 'camera' else options[key])
    view.studio_values = dict(values)
    view.studio_camera = values['camera']


def sync_scene_studio(panel, fixed_camera=False, fixed_key=None):
    options = panel.model.studio_draw(keep=True, fixed_camera=fixed_camera, fixed_key=fixed_key)
    for key, value in panel.model.values.items():
        if panel.values[key].get() != value:
            panel.values[key].set(value)
        panel.combos[key].configure(values=ANGLES if key == 'camera' else options[key])
    panel.studio_values = dict(panel.model.values)
    panel.studio_camera = panel.model.values['camera']


def opening_camera_changed(view):
    if view.render_style.get() != CLOSEUP:
        return
    try:
        sync_opening_studio(view, fixed_camera=True)
    except ShotConflict as exc:
        view.values['camera'].set(view.studio_camera)
        messagebox.showwarning('近景镜头', str(exc), parent=view)


def scene_camera_changed(panel):
    if panel.model.render_style != CLOSEUP:
        return
    panel.capture()
    try:
        sync_scene_studio(panel, fixed_camera=True)
    except ShotConflict as exc:
        panel.model.values['camera'] = panel.studio_camera
        panel.values['camera'].set(panel.studio_camera)
        messagebox.showwarning('近景镜头', str(exc), parent=panel)

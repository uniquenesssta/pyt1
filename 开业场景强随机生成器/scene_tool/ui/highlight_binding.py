"""Apply either highlight choice immediately; the other follows unless locked."""
from tkinter import messagebox
from scene_tool.config.closeup import CLOSEUP
from scene_tool.generation.studio_shots import ShotConflict
from scene_tool.ui.studio_binding import sync_opening_studio, sync_scene_studio


def bind_highlight(view, key, *, scene=False):
    def apply(_event):
        style = view.model.render_style if scene else view.render_style.get()
        if style != CLOSEUP or not view.combos[key].winfo_exists():
            return
        current = view.values[key].get().strip()
        previous = getattr(view, 'studio_values', {}).get(key)
        if current == previous:
            return
        if scene:
            view.capture()
        try:
            if scene:
                sync_scene_studio(view, fixed_key=key)
            else:
                sync_opening_studio(view, fixed_key=key)
        except ShotConflict as exc:
            if previous is not None:
                view.values[key].set(previous)
                if scene:
                    view.capture()
            messagebox.showwarning('反光与位置', str(exc), parent=view)

    for event in ('<<ComboboxSelected>>', '<Return>', '<FocusOut>'):
        view.combos[key].bind(event, apply, add='+')

"""Apply visibility changes through the same prompt controllers as editing."""
def change_opening(view, key):
    if not view.refresh(force=True):
        view.hidden[key].set(not view.hidden[key].get())
        return
    view.prompt_reset.snapshot = None
    view.undo_reset_button.configure(state='disabled')
    view.save()


def change_scene(panel, key):
    if not panel.allow_replace():
        panel.hidden[key].set(not panel.hidden[key].get())
        panel.capture()
        return
    panel.model.regenerate()
    panel.model.undo = None
    panel.show_prompt()
    panel.persist()

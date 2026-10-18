from tkinter.scrolledtext import ScrolledText
from scene_tool.config.defaults import DEFAULT_CONSTRAINTS
from scene_tool.ui.components.prompt_editor import prompt_editor


def build_prompt_panel(self, parent):
    self.prompt, self.extra, _ = prompt_editor(parent)
    # Retain the saved rule editor; it is displayed in the settings dialog.
    self.constraints = ScrolledText(parent, wrap='word', undo=True)
    self.constraints.insert('1.0', DEFAULT_CONSTRAINTS)
    self.extra.bind('<KeyRelease>', self.schedule_refresh)

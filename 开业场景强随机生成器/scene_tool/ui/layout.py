from tkinter import ttk
from scene_tool.ui.parameter_panel import build_parameters
from scene_tool.ui.prompt_panel import build_prompt_panel
from scene_tool.ui.components.workbench import workbench, actions, MenuAction
from scene_tool.ui.settings_dialog import open_settings


def build_ui(self):
    self.content_surface = ttk.Frame(self, padding=20)
    self.content_surface.place(x=0, y=0, relwidth=1, relheight=1)
    status = ttk.Label(self.content_surface, textvariable=self.status, wraplength=850)
    status.pack(side='bottom', fill='x', pady=(8, 0))
    left, right, footer = workbench(self.content_surface)
    build_parameters(self, left)
    build_prompt_panel(self, right)
    menu = actions(footer, self.randomize, self.copy_prompt, self.unlock,
                   lambda: self.refresh(force=True), self.export,
                   self.prompt_reset.reset, self.prompt_reset.undo)
    self.undo_reset_button = MenuAction(menu, 3)
    self.undo_reset_button.configure(state='disabled')
    menu.add_separator()
    menu.add_command(label='开业场景设置', command=lambda: open_settings(self))
    menu.add_command(label='编辑参数池', command=self.edit_pools)

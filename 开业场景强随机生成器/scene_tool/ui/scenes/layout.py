import tkinter as tk
from tkinter import ttk
from scene_tool.ui.components.results import ResultList
from scene_tool.ui.components.workbench import workbench, actions
from scene_tool.ui.components.prompt_editor import prompt_editor


def build_panel(panel):
    left, right, footer = workbench(panel)
    results = ResultList(left)
    panel.values, panel.locks, panel.combos = {}, {}, {}
    dimensions = panel.model.profile['dimensions']
    groups = [('环境空间', dimensions[:2] + dimensions[3:5]),
              ('装置与人物', [dimensions[2], dimensions[5], dimensions[6]]),
              ('拍摄', dimensions[7:])]
    for title, fields in groups:
        results.group(title)
        for dimension in fields:
            key = dimension['key']
            panel.values[key] = tk.StringVar(value=panel.model.values[key])
            panel.locks[key] = tk.BooleanVar(value=panel.model.locks[key])
            results.result(dimension['label'], panel.values[key], panel.locks[key])
    panel.prompt, panel.extra, header = prompt_editor(right)
    panel.prompt.insert('1.0', panel.model.prompt)
    panel.extra.insert('1.0', panel.model.extra)
    panel.sync_status = tk.StringVar(value='已同步')
    ttk.Label(header, textvariable=panel.sync_status, foreground='#737b8a').pack(side='right')
    menu = actions(footer, panel.randomize, panel.copy, panel.unlock, panel.update_prompt,
            panel.export, panel.reset, panel.undo_reset)
    menu.add_separator()
    menu.add_command(label='编辑本场景参数池', command=panel.edit_pools)

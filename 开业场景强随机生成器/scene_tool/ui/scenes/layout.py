import tkinter as tk
from tkinter import ttk
from scene_tool.config.product_size import PRODUCT_SIZE_CHOICES
from scene_tool.ui.components.results import ResultList
from scene_tool.ui.visibility_binding import change_scene
from scene_tool.ui.components.workbench import workbench, actions
from scene_tool.ui.components.prompt_editor import prompt_editor


def build_panel(panel):
    left, right, footer = workbench(panel)
    results = ResultList(left)
    panel.values, panel.locks, panel.combos, panel.hidden = {}, {}, {}, {}
    panel.product_size = tk.StringVar(value=panel.model.product_size)
    results.group('产品规格（不参与随机）')
    results.result('产品尺寸 / 比例', panel.product_size, None, choices=PRODUCT_SIZE_CHOICES)
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
            panel.hidden[key] = tk.BooleanVar(value=panel.model.hidden[key])
            label = results.result(dimension['label'], panel.values[key], panel.locks[key],
                                   choices=panel.model.pools[key], hidden=panel.hidden[key],
                                   on_hide=lambda k=key: change_scene(panel, k))
            panel.combos[key] = label.editor
    panel.prompt, panel.extra, header = prompt_editor(right)
    panel.prompt.insert('1.0', panel.model.prompt)
    panel.extra.insert('1.0', panel.model.extra)
    panel.sync_status = tk.StringVar(value='已同步')
    ttk.Label(header, textvariable=panel.sync_status, foreground='#737b8a').pack(side='right')
    menu = actions(footer, panel.randomize, panel.copy, panel.unlock, panel.update_prompt,
            panel.export, panel.reset, panel.undo_reset)
    menu.add_separator()
    menu.add_command(label='编辑本场景参数池', command=panel.edit_pools)


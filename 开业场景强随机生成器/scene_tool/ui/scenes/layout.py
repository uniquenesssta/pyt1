import tkinter as tk
from scene_tool.config import surface_reflection as reflection
from tkinter import ttk
from scene_tool.ui.components.product_size import product_size_row
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
    panel.size_row = product_size_row(results, panel.product_size).master
    panel.close_subject = tk.StringVar(value=panel.model.close_subject)
    panel.subject_row = results.result('拍摄对象', panel.close_subject, None).master
    # Share one grid slot so switching style does not leave an empty row.
    results.rowconfigure(results.next_row - 1, weight=0, uniform='')
    panel.subject_row.grid_configure(row=results.next_row - 2)
    panel.close_material = tk.StringVar(value=panel.model.close_material)
    panel.material_row_index = results.next_row
    panel.material_row = results.result('自定义材质', panel.close_material, None).master
    panel.parameter_labels = {}
    dimensions = panel.model.active_profile()['dimensions']
    if not any(d['key'] == reflection.KEY for d in dimensions):
        dimensions = [*dimensions, reflection.dimension()]
    groups = [('环境空间', dimensions[:2] + dimensions[3:5]),
              ('装置与人物', [dimensions[2], dimensions[5], dimensions[6]]),
              ('拍摄', dimensions[7:])]
    panel.group_labels = []
    for title, fields in groups:
        panel.group_labels.append(results.group(title))
        for dimension in fields:
            key = dimension['key']
            panel.values[key] = tk.StringVar(value=panel.model.values.get(key, reflection.OPTIONS[0]))
            panel.locks[key] = tk.BooleanVar(value=panel.model.locks.get(key, False))
            panel.hidden[key] = tk.BooleanVar(value=panel.model.hidden.get(key, False))
            label = results.result(dimension['label'], panel.values[key], panel.locks[key],
                                   choices=panel.model.pools.get(key, dimension['options']), readonly=key == 'camera', hidden=panel.hidden[key],
                                   on_hide=lambda k=key: change_scene(panel, k))
            if key == reflection.KEY:
                panel.reflection_row = label.master
                panel.reflection_row_index = results.next_row - 1
            panel.parameter_labels[key] = label
            panel.combos[key] = label.editor
            if key == 'camera':
                from scene_tool.ui.studio_binding import scene_camera_changed
                label.editor.bind('<<ComboboxSelected>>', lambda _: scene_camera_changed(panel))
    panel.prompt, panel.extra, header = prompt_editor(right)
    panel.prompt.insert('1.0', panel.model.prompt)
    panel.extra.insert('1.0', panel.model.extra)
    panel.sync_status = tk.StringVar(value='已同步')
    ttk.Label(header, textvariable=panel.sync_status, foreground='#737b8a').pack(side='right')
    menu = actions(footer, panel.randomize, panel.copy, panel.unlock, panel.update_prompt,
            panel.export, panel.reset, panel.undo_reset)
    menu.add_separator()
    menu.add_command(label='编辑本场景参数池', command=panel.edit_pools)


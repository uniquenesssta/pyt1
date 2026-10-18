import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText


def build_panel(panel):
    panel.columnconfigure(0, weight=1)
    panel.columnconfigure(1, weight=1)
    panel.rowconfigure(1, weight=1)
    ttk.Label(panel, text=panel.model.profile['name'] + ' · 10维强随机', font=('Microsoft YaHei UI', 18, 'bold')).grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 14))
    left = ttk.Frame(panel)
    left.grid(row=1, column=0, sticky='nsew', padx=(0, 18))
    left.columnconfigure(1, weight=1)
    panel.values, panel.locks, panel.combos = {}, {}, {}
    for row, dimension in enumerate(panel.model.profile['dimensions']):
        key = dimension['key']
        panel.values[key] = tk.StringVar(value=panel.model.values[key])
        panel.locks[key] = tk.BooleanVar(value=panel.model.locks[key])
        ttk.Label(left, text=f'{row + 1:02d}  {dimension["label"]}').grid(row=row, column=0, sticky='w', pady=8, padx=(0, 8))
        combo = ttk.Combobox(left, textvariable=panel.values[key], values=panel.model.pools[key], width=28)
        combo.grid(row=row, column=1, sticky='ew')
        panel.combos[key] = combo
        ttk.Checkbutton(left, text='锁定', variable=panel.locks[key]).grid(row=row, column=2)
    buttons = ttk.Frame(left)
    buttons.grid(row=10, column=0, columnspan=3, sticky='w', pady=16)
    ttk.Button(buttons, text='重新随机', style='Primary.TButton', command=panel.randomize).pack(side='left')
    ttk.Button(buttons, text='全部解锁', command=panel.unlock).pack(side='left', padx=6)
    ttk.Button(buttons, text='编辑参数池', command=panel.edit_pools).pack(side='left')
    ttk.Label(left, text='各维独立轮换，候选用完再重复。\n本场景的参数、锁定与手改提示词单独保存。\n参考图内容默认保留；仅生成可复制的提示词。', wraplength=440).grid(row=11, column=0, columnspan=3, sticky='w')
    right = ttk.Frame(panel)
    right.grid(row=1, column=1, sticky='nsew')
    tabs = ttk.Notebook(right)
    tabs.pack(fill='both', expand=True)
    prompt_tab, extra_tab = ttk.Frame(tabs), ttk.Frame(tabs)
    tabs.add(prompt_tab, text='完整提示词')
    tabs.add(extra_tab, text='补充要求')
    panel.prompt = ScrolledText(prompt_tab, wrap='word', undo=True, width=35, font=('Microsoft YaHei UI', 11))
    panel.prompt.pack(fill='both', expand=True)
    panel.extra = ScrolledText(extra_tab, wrap='word', undo=True, width=35, font=('Microsoft YaHei UI', 11))
    panel.extra.pack(fill='both', expand=True)
    panel.extra.insert('1.0', panel.model.extra)
    panel.prompt.insert('1.0', panel.model.prompt)
    actions = ttk.Frame(right)
    actions.pack(fill='x', pady=(10, 0))
    for label, callback, style in [('复制提示词', panel.copy, 'Primary.TButton'), ('更新提示词', panel.update_prompt, 'TButton'), ('导出TXT', panel.export, 'TButton')]:
        ttk.Button(actions, text=label, command=callback, style=style).pack(side='left', padx=(0, 6))
    resets = ttk.Frame(right)
    resets.pack(fill='x', pady=8)
    ttk.Button(resets, text='复原默认提示词', command=panel.reset).pack(side='left')
    ttk.Button(resets, text='撤销复原', command=panel.undo_reset).pack(side='left', padx=6)

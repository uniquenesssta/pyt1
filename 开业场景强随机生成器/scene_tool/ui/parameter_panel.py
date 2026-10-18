from tkinter import ttk
from scene_tool.config.defaults import DIMENSIONS, INDUSTRIES

def build_parameters(self, body):
    left = ttk.Frame(body, padding=(0, 0, 20, 0))
    left.grid(row=0, column=0, sticky='nsew')
    left.columnconfigure(1, weight=1)
    ttk.Label(left, text='随机参数', font=('Microsoft YaHei UI', 13, 'bold')).grid(row=0, column=0, sticky='w', pady=(0, 12))
    ttk.Checkbutton(left, text='强随机轮换', variable=self.strong).grid(row=0, column=1, sticky='e')
    ttk.Label(left, text='锁定').grid(row=0, column=2, padx=(10, 0))
    self.combos = {}
    extra_row = len(DIMENSIONS) + 1
    for row, (key, label) in enumerate(DIMENSIONS, 1):
        ttk.Label(left, text=f'{row:02d}  {label}').grid(row=row, column=0, sticky='w', pady=5, padx=(0, 10))
        combo = ttk.Combobox(left, textvariable=self.values[key], values=self.engine.pools[key], width=25)
        combo.grid(row=row, column=1, sticky='ew')
        self.combos[key] = combo
        ttk.Checkbutton(left, variable=self.locks[key]).grid(row=row, column=2, padx=(10, 0))
    ttk.Label(left, text='行业 / 自定义').grid(row=extra_row + 0, column=0, sticky='w', pady=(18, 7))
    ttk.Combobox(left, textvariable=self.industry, values=INDUSTRIES).grid(row=extra_row + 0, column=1, columnspan=2, sticky='ew', pady=(18, 7))
    ttk.Label(left, text='开业文案').grid(row=extra_row + 1, column=0, sticky='w', pady=7)
    ttk.Entry(left, textvariable=self.copyline).grid(row=extra_row + 1, column=1, sticky='ew')
    ttk.Checkbutton(left, variable=self.copy_locked).grid(row=extra_row + 1, column=2, padx=(10, 0))
    copy_controls = ttk.Frame(left)
    copy_controls.grid(row=extra_row + 2, column=0, columnspan=3, sticky='ew')
    ttk.Checkbutton(copy_controls, text='随机开业文案（100条主标题 × 100条副句）', variable=self.copy_random).pack(side='left')
    controls = ttk.Frame(left)
    controls.grid(row=extra_row + 3, column=0, columnspan=3, sticky='ew', pady=(16, 8))
    ttk.Button(controls, text='重新随机', style='Primary.TButton', command=self.randomize).pack(side='left')
    ttk.Button(controls, text='全部解锁', command=self.unlock).pack(side='left', padx=8)
    ttk.Button(controls, text='编辑参数池', command=self.edit_pools).pack(side='left')
    ttk.Checkbutton(left, text='品牌和街道随机组合（关闭则使用候选池）', variable=self.generated_names).grid(row=extra_row + 4, column=0, columnspan=3, sticky='w')
    ttk.Label(left, text='品牌：西文音节与中文同步生成；街道：词根＋门牌号。\n其余维度独立轮换。地址为虚构示例，所有参数均可编辑。', wraplength=460).grid(row=extra_row + 5, column=0, columnspan=3, sticky='w', pady=10)

import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
from scene_tool.config.defaults import DIMENSIONS
from scene_tool.ui.style_binding import sync_style
from scene_tool.domain.scene_pools import EXTRA_LABELS
from scene_tool.domain.pools import validate_pools
from scene_tool.storage.pools import save_pools
from scene_tool.generation.parameters import Randomizer

def edit_pools(self):
    dialog = tk.Toplevel(self)
    dialog.title(self.industry.get() + ' · ' + self.render_style.get() + ' · 候选池')
    dialog.geometry('700x620')
    dialog.transient(self)
    dialog.grab_set()
    ttk.Label(dialog, text='编辑当前行业、室内外和提示词风格的候选；每项至少两条。镜头由拍摄模式管理。', padding=12).pack(anchor='w')
    from scene_tool.domain.industry_profiles import dimensions, industry_key
    from scene_tool.domain.scene_pools import pool_key
    style, industry, environment = self.render_style.get(), self.industry.get(), self.values['environment'].get()
    dims = [d for d in dimensions(style) if d[0] not in ('camera', 'environment')]
    label_to_key = {label: key for key, label in dims}
    selected = tk.StringVar(value=dims[0][1])
    selector = ttk.Combobox(dialog, textvariable=selected, values=list(label_to_key), state='readonly')
    selector.pack(fill='x', padx=12)
    editor = ScrolledText(dialog, wrap='word', font=('Microsoft YaHei UI', 11))
    editor.pack(fill='both', expand=True, padx=12, pady=12)
    scoped = self.engine.scoped_pools(industry, environment, style)
    working = {k: list(scoped.get(k, self.engine.pools.get(pool_key(k, environment), []))) for k, _ in dims}
    active = [dims[0][0]]
    editor.insert('1.0', '\n'.join(working[active[0]]))
    def capture():
        working[active[0]] = [s.strip() for s in editor.get('1.0', 'end-1c').splitlines() if s.strip()]
    def change(_):
        capture()
        active[0] = label_to_key[selected.get()]
        editor.delete('1.0', 'end')
        editor.insert('1.0', '\n'.join(working[active[0]]))
    selector.bind('<<ComboboxSelected>>', change)
    def save():
        capture()
        if any(len(set(items)) < 2 for items in working.values()):
            messagebox.showerror('无法保存参数池', '每项至少需要两个不同候选。', parent=dialog)
            return
        context = '|'.join((industry_key(industry), environment or '室外', style or ''))
        previous = self.engine.industry_overrides.get(context)
        self.engine.industry_overrides[context] = {k: list(dict.fromkeys(v)) for k, v in working.items()}
        if not self.save():
            if previous is None:
                self.engine.industry_overrides.pop(context, None)
            else:
                self.engine.industry_overrides[context] = previous
            return
        sync_style(self)
        dialog.destroy()
        self.save()
        self.status.set('参数池已保存，下一次随机使用新选项。')
    ttk.Button(dialog, text='保存全部参数池', command=save).pack(pady=(0, 12))


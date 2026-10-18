import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
from scene_tool.config.defaults import DIMENSIONS
from scene_tool.domain.pools import validate_pools
from scene_tool.storage.pools import save_pools
from scene_tool.generation.parameters import Randomizer

def edit_pools(self):
    dialog = tk.Toplevel(self)
    dialog.title('编辑12维参数池')
    dialog.geometry('700x620')
    dialog.transient(self)
    dialog.grab_set()
    ttk.Label(dialog, text='每行一个候选值；每维至少两项。品牌和街道池仅在关闭随机组合时使用。', padding=12).pack(anchor='w')
    label_to_key = {label: key for key, label in DIMENSIONS}
    selected = tk.StringVar(value=DIMENSIONS[0][1])
    selector = ttk.Combobox(dialog, textvariable=selected, values=list(label_to_key), state='readonly')
    selector.pack(fill='x', padx=12)
    editor = ScrolledText(dialog, wrap='word', font=('Microsoft YaHei UI', 11))
    editor.pack(fill='both', expand=True, padx=12, pady=12)
    working = {k: list(v) for k, v in self.engine.pools.items()}
    active = [DIMENSIONS[0][0]]
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
        try:
            pools = validate_pools(working)
            save_pools(self.pool_path, pools)
        except (OSError, ValueError) as exc:
            messagebox.showerror('无法保存参数池', str(exc), parent=dialog)
            return
        old_engine = self.engine
        self.engine = Randomizer(pools, generated=self.generated_names.get())
        self.engine.restore_recent(old_engine.recent)
        self.engine.restore_bags({k: v for k, v in old_engine.bags.items()
                                  if old_engine.pools[k] == pools[k]})
        for key, combo in self.combos.items():
            combo.configure(values=pools[key])
        dialog.destroy()
        self.save()
        self.status.set('参数池已保存，下一次随机使用新选项。')
    ttk.Button(dialog, text='保存全部参数池', command=save).pack(pady=(0, 12))

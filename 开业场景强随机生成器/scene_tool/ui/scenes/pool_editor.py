import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText


def edit_pool(panel):
    model = panel.model
    dialog = tk.Toplevel(panel)
    dialog.title(model.profile['name'] + ' · 候选池')
    dialog.geometry('720x540')
    dialog.transient(panel.winfo_toplevel())
    dialog.grab_set()
    dimensions = model.profile['dimensions']
    names = {d['label']: d['key'] for d in dimensions}
    selected = tk.StringVar(value=dimensions[0]['label'])
    selector = ttk.Combobox(dialog, textvariable=selected, values=list(names), state='readonly')
    selector.pack(fill='x', padx=12, pady=12)
    editor = ScrolledText(dialog, wrap='word')
    editor.pack(fill='both', expand=True, padx=12)
    working = {k: list(v) for k, v in model.pools.items()}
    active = [dimensions[0]['key']]
    editor.insert('1.0', '\n'.join(working[active[0]]))
    def capture():
        working[active[0]] = editor.get('1.0', 'end-1c').splitlines()
    def change(_):
        capture()
        active[0] = names[selected.get()]
        editor.delete('1.0', 'end')
        editor.insert('1.0', '\n'.join(working[active[0]]))
    selector.bind('<<ComboboxSelected>>', change)
    def save():
        capture()
        if any(len(set(x.strip() for x in items if x.strip())) < 2 for items in working.values()):
            messagebox.showerror('候选不足', '每项至少需要两个不同候选。', parent=dialog)
            return
        for key, items in working.items():
            model.set_pool(key, items)
            panel.combos[key].configure(values=model.pools[key])
        panel.persist()
        dialog.destroy()
    ttk.Button(dialog, text='保存本场景候选池', command=save).pack(pady=12)

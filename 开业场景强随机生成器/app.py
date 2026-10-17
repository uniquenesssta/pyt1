"""Run with python app.py. Offline desktop prompt generator; no external packages."""
from __future__ import annotations

import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText

from core import (DIMENSIONS, INDUSTRIES, DEFAULT_CONSTRAINTS, Randomizer,
                  load_pools, validate_pools, atomic_json, make_prompt, upgrade_pools)

BASE = Path(__file__).resolve().parent
DATA = BASE / 'data'


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('11维强随机 · 开业场景提示词')
        self.geometry('1180x800')
        self.minsize(940, 660)
        self.configure(bg='#f3f5fa')
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('.', font=('Microsoft YaHei UI', 10))
        style.configure('TFrame', background='#f3f5fa')
        style.configure('TLabel', background='#f3f5fa', foreground='#24324b')
        style.configure('TCheckbutton', background='#f3f5fa')
        style.configure('TButton', padding=(12, 7))
        style.configure('Primary.TButton', background='#6357df', foreground='white')
        style.map('Primary.TButton', background=[('active', '#5043c5')])
        self.values = {k: tk.StringVar() for k, _ in DIMENSIONS}
        self.locks = {k: tk.BooleanVar() for k, _ in DIMENSIONS}
        self.industry = tk.StringVar(value='美业')
        self.copyline = tk.StringVar(value='盛大开业 · 美好启幕')
        self.strong = tk.BooleanVar(value=True)
        self.generated_names = tk.BooleanVar(value=True)
        self.status = tk.StringVar(value='')
        self.rendered = ''
        self.ready = False
        self.pending = None
        self.pool_path = DATA / 'custom_pools.json'
        self.startup_errors = []
        try:
            pools = load_pools(self.pool_path if self.pool_path.exists() else BASE / 'pools.json')
        except (OSError, ValueError) as exc:
            pools = load_pools(BASE / 'pools.json')
            self.startup_errors.append(f'自定义参数池无法读取，已使用默认池。\n{exc}')
        pools = upgrade_pools(pools, load_pools(BASE / 'pools.json'),
                              json.loads((BASE / 'legacy_pools_v1.json').read_text(encoding='utf-8')))
        self.engine = Randomizer(pools)
        self.build_ui()
        self.restore()
        self.ready = True
        for var in [*self.values.values(), self.industry, self.copyline]:
            var.trace_add('write', self.schedule_refresh)
        if not all(v.get() for v in self.values.values()):
            self.randomize()
        elif not self.prompt.get('1.0', 'end-1c'):
            self.refresh()
        self.protocol('WM_DELETE_WINDOW', self.close)
        for error in self.startup_errors:
            self.after_idle(lambda e=error: messagebox.showwarning('读取设置', e, parent=self))

    def build_ui(self):
        header = ttk.Frame(self, padding=(24, 18))
        header.pack(fill='x')
        ttk.Label(header, text='开业场景 · 11维强随机', font=('Microsoft YaHei UI', 21, 'bold')).pack(anchor='w')
        ttk.Label(header, text='独立抽取每一维，让场景真正换一种样子。抽取 → 编辑 → 复制提示词').pack(anchor='w', pady=(5, 0))
        body = ttk.Frame(self, padding=(24, 0, 24, 12))
        body.pack(fill='both', expand=True)
        body.columnconfigure(0, weight=1, uniform='cols')
        body.columnconfigure(1, weight=1, uniform='cols')
        body.rowconfigure(0, weight=1)
        left = ttk.Frame(body, padding=(0, 0, 20, 0))
        left.grid(row=0, column=0, sticky='nsew')
        left.columnconfigure(1, weight=1)
        ttk.Label(left, text='随机参数', font=('Microsoft YaHei UI', 13, 'bold')).grid(row=0, column=0, sticky='w', pady=(0, 12))
        ttk.Checkbutton(left, text='强随机轮换', variable=self.strong).grid(row=0, column=1, sticky='e')
        ttk.Label(left, text='锁定').grid(row=0, column=2, padx=(10, 0))
        self.combos = {}
        for row, (key, label) in enumerate(DIMENSIONS, 1):
            ttk.Label(left, text=f'{row:02d}  {label}').grid(row=row, column=0, sticky='w', pady=7, padx=(0, 10))
            combo = ttk.Combobox(left, textvariable=self.values[key], values=self.engine.pools[key], width=25)
            combo.grid(row=row, column=1, sticky='ew')
            self.combos[key] = combo
            ttk.Checkbutton(left, variable=self.locks[key]).grid(row=row, column=2, padx=(10, 0))
        ttk.Label(left, text='行业 / 自定义').grid(row=12, column=0, sticky='w', pady=(18, 7))
        ttk.Combobox(left, textvariable=self.industry, values=INDUSTRIES).grid(row=12, column=1, columnspan=2, sticky='ew', pady=(18, 7))
        ttk.Label(left, text='开业文案').grid(row=13, column=0, sticky='w', pady=7)
        ttk.Entry(left, textvariable=self.copyline).grid(row=13, column=1, columnspan=2, sticky='ew')
        controls = ttk.Frame(left)
        controls.grid(row=14, column=0, columnspan=3, sticky='ew', pady=(16, 8))
        ttk.Button(controls, text='重新随机', style='Primary.TButton', command=self.randomize).pack(side='left')
        ttk.Button(controls, text='全部解锁', command=self.unlock).pack(side='left', padx=8)
        ttk.Button(controls, text='编辑参数池', command=self.edit_pools).pack(side='left')
        ttk.Checkbutton(left, text='品牌和街道随机组合（关闭则使用候选池）', variable=self.generated_names).grid(row=15, column=0, columnspan=3, sticky='w')
        ttk.Label(left, text='品牌：西文音节与中文同步生成；街道：词根＋门牌号。\n其余维度独立轮换。地址为虚构示例，所有参数均可编辑。', wraplength=460).grid(row=16, column=0, columnspan=3, sticky='w', pady=10)
        right = ttk.Frame(body)
        right.grid(row=0, column=1, sticky='nsew')
        tabs = ttk.Notebook(right)
        tabs.pack(fill='both', expand=True)
        prompt_tab, rules_tab = ttk.Frame(tabs), ttk.Frame(tabs)
        tabs.add(prompt_tab, text='  完整提示词  ')
        tabs.add(rules_tab, text='  固定要求 / 补充  ')
        self.prompt = ScrolledText(prompt_tab, wrap='word', undo=True, font=('Microsoft YaHei UI', 11), padx=14, pady=14, relief='flat', width=35, height=15)
        self.prompt.pack(fill='both', expand=True, pady=(8, 0))
        ttk.Label(rules_tab, text='固定要求（默认保留原图紫色背景和3.5×2.2米大板）').pack(anchor='w', pady=10)
        self.constraints = ScrolledText(rules_tab, wrap='word', font=('Microsoft YaHei UI', 10), height=14, width=35, undo=True)
        self.constraints.pack(fill='both', expand=True)
        self.constraints.insert('1.0', DEFAULT_CONSTRAINTS)
        ttk.Label(rules_tab, text='补充要求').pack(anchor='w', pady=10)
        self.extra = ScrolledText(rules_tab, wrap='word', font=('Microsoft YaHei UI', 10), height=5, width=35, undo=True)
        self.extra.pack(fill='both', expand=True)
        for widget in (self.constraints, self.extra):
            widget.bind('<KeyRelease>', self.schedule_refresh)
        actions = ttk.Frame(right, padding=(0, 12, 0, 0))
        actions.pack(fill='x')
        ttk.Button(actions, text='复制提示词', style='Primary.TButton', command=self.copy_prompt).pack(side='left')
        ttk.Button(actions, text='更新提示词', command=lambda: self.refresh(force=True)).pack(side='left', padx=8)
        ttk.Button(actions, text='导出 TXT', command=self.export).pack(side='left')
        ttk.Label(self, textvariable=self.status, padding=(24, 8), wraplength=1100).pack(fill='x')

    def current(self):
        return {k: v.get().strip() for k, v in self.values.items()}

    def generated(self):
        return make_prompt(self.current(), self.industry.get(), self.constraints.get('1.0', 'end-1c'),
                           self.copyline.get(), self.extra.get('1.0', 'end-1c'))

    def edited(self):
        return self.prompt.get('1.0', 'end-1c') != self.rendered

    def schedule_refresh(self, *_):
        if not self.ready:
            return
        if self.pending:
            self.after_cancel(self.pending)
        self.pending = self.after(250, self.refresh)

    def refresh(self, force=False):
        self.pending = None
        if self.edited():
            if not force:
                self.status.set('提示词有手动编辑，已保留；参数变动后请点“更新提示词”重新组成，或直接复制当前文字。')
                return False
            if not messagebox.askyesno('更新提示词', '根据当前参数重新组成提示词，会替换右侧的手动编辑。继续吗？', parent=self):
                return False
        try:
            content = self.generated()
        except ValueError as exc:
            self.status.set(str(exc))
            return False
        self.set_prompt(content)
        self.status.set('提示词已更新。复制后与参考图一并提交；本工具离线运行，只生成文字。')
        return True

    def set_prompt(self, content):
        self.prompt.delete('1.0', 'end')
        self.prompt.insert('1.0', content)
        self.rendered = content

    def randomize(self):
        locked = [k for k, v in self.locks.items() if v.get()]
        if len(locked) == len(DIMENSIONS):
            self.status.set('11项已全部锁定，请解锁需要重新抽取的参数。')
            return
        if self.edited() and not messagebox.askyesno('重新随机', '重新随机会生成新提示词，并替换右侧手动编辑。继续吗？', parent=self):
            return
        if self.pending:
            self.after_cancel(self.pending)
            self.pending = None
        self.engine.generated = self.generated_names.get()
        values = self.engine.draw(self.current(), locked, self.strong.get())
        self.ready = False
        for key, value in values.items():
            self.values[key].set(value)
        self.ready = True
        self.rendered = self.prompt.get('1.0', 'end-1c')
        self.refresh()
        self.save()

    def unlock(self):
        for value in self.locks.values():
            value.set(False)
        self.status.set('已全部解锁。')

    def copy_prompt(self):
        self.flush_refresh()
        text = self.prompt.get('1.0', 'end-1c')
        if not text.strip():
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update_idletasks()
        self.status.set('已复制当前完整提示词，可以粘贴并附上参考图。')

    def flush_refresh(self):
        if self.pending:
            self.after_cancel(self.pending)
            self.pending = None
            self.refresh()

    def export(self):
        self.flush_refresh()
        path = filedialog.asksaveasfilename(parent=self, title='导出提示词', defaultextension='.txt', initialfile='开业场景提示词.txt', filetypes=[('文本文件', '*.txt')])
        if path:
            try:
                Path(path).write_text(self.prompt.get('1.0', 'end-1c'), encoding='utf-8-sig')
                self.status.set(f'已导出：{path}')
            except OSError as exc:
                messagebox.showerror('导出失败', str(exc), parent=self)

    def edit_pools(self):
        dialog = tk.Toplevel(self)
        dialog.title('编辑11维参数池')
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
                atomic_json(self.pool_path, pools)
            except (OSError, ValueError) as exc:
                messagebox.showerror('无法保存参数池', str(exc), parent=dialog)
                return
            self.engine = Randomizer(pools)
            for key, combo in self.combos.items():
                combo.configure(values=pools[key])
            dialog.destroy()
            self.save()
            self.status.set('参数池已保存，下一次随机使用新选项。')
        ttk.Button(dialog, text='保存全部参数池', command=save).pack(pady=(0, 12))

    def save(self):
        state = {'values': self.current(), 'locks': {k: v.get() for k, v in self.locks.items()},
                 'generated_names': self.generated_names.get(), 'recent': self.engine.recent,
                 'strong': self.strong.get(), 'industry': self.industry.get(), 'copy': self.copyline.get(),
                 'constraints': self.constraints.get('1.0', 'end-1c'), 'extra': self.extra.get('1.0', 'end-1c'),
                 'prompt': self.prompt.get('1.0', 'end-1c'), 'rendered': self.rendered, 'bags': self.engine.bags}
        try:
            atomic_json(DATA / 'state.json', state)
            return True
        except OSError as exc:
            self.status.set(f'设置保存失败（仍可复制提示词）：{exc}')
            return False

    def restore(self):
        path = DATA / 'state.json'
        if not path.exists():
            return
        try:
            state = json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(state, dict):
                raise ValueError('设置应为对象')
            for section in ('values', 'locks'):
                if not isinstance(state.get(section, {}), dict):
                    raise ValueError(f'{section} 格式错误')
            for key, value in state.get('values', {}).items():
                if key in self.values and isinstance(value, str):
                    self.values[key].set(value)
            for key, value in state.get('locks', {}).items():
                if key in self.locks and isinstance(value, bool):
                    self.locks[key].set(value)
            for name, variable in [('industry', self.industry), ('copy', self.copyline)]:
                if isinstance(state.get(name), str):
                    variable.set(state[name])
            if isinstance(state.get('strong'), bool):
                self.strong.set(state['strong'])
            for name, widget in [('constraints', self.constraints), ('extra', self.extra), ('prompt', self.prompt)]:
                if isinstance(state.get(name), str):
                    widget.delete('1.0', 'end')
                    widget.insert('1.0', state[name])
            self.rendered = state.get('rendered', '') if isinstance(state.get('rendered', ''), str) else ''
            self.engine.restore_bags(state.get('bags'))
            self.engine.restore_recent(state.get('recent'))
            if isinstance(state.get('generated_names'), bool):
                self.generated_names.set(state['generated_names'])
            self.status.set('已恢复上次参数与提示词。点击“重新随机”生成下一组。')
        except (OSError, ValueError) as exc:
            self.startup_errors.append(f'上次设置无法读取，已尽可能恢复有效内容。\n{exc}')

    def close(self):
        self.flush_refresh()
        if not self.save() and not messagebox.askyesno('设置保存失败', '无法保存当前设置，仍要退出吗？可以先复制或导出提示词。', parent=self):
            return
        self.destroy()


if __name__ == '__main__':
    App().mainloop()

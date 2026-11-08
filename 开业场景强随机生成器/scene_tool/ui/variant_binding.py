"""Connect draft selection to actual parameters, prompt, shuffle bags and persistence."""
import copy
from tkinter import messagebox
from scene_tool.domain.variants.generation import opening_variants, scene_variants, clone_rng
from scene_tool.ui.variant_dialog import show_variants
from scene_tool.ui.style_binding import sync_style


def open_opening_variants(view):
    try:
        candidates = opening_variants(view.engine,view.current(),
            {k for k,v in view.locks.items() if v.get()},style=view.render_style.get(),
            industry=view.industry.get(),constraints=view.constraints.get('1.0','end-1c'),
            copyline=view.copyline.get(),extra=view.extra.get('1.0','end-1c'),
            hidden={k for k,v in view.hidden.items() if v.get()},
            product_size=view.product_size.get(),strong=view.strong.get(),
            generated=view.generated_names.get())
    except ValueError as exc:
        messagebox.showwarning('无法生成方案',str(exc),parent=view)
        return
    def apply(item):
        if view.edited() and not messagebox.askyesno('应用方案','应用后替换右侧手改提示词，继续吗？',parent=view):
            return False
        if view.pending:
            view.after_cancel(view.pending)
            view.pending=None
        view.ready=False
        view.engine=item.payload['engine']
        for key,value in item.payload['values'].items(): view.values[key].set(value)
        sync_style(view, preserve_values=True)
        view.ready=True
        view.set_prompt(item.prompt)
        view.prompt_reset.snapshot=None
        view.undo_reset_button.configure(state='disabled')
        view.save()
        view.status.set('已应用所选方案；锁定与隐藏设置保持。')
        return True
    show_variants(view,candidates,apply)


def open_scene_variants(panel):
    panel.pause()
    try:
        candidates=scene_variants(panel.model)
    except ValueError as exc:
        messagebox.showwarning('无法生成方案',str(exc),parent=panel)
        return
    def apply(item):
        if not panel.allow_replace(): return False
        panel.updating=True
        panel.model.values=dict(item.payload['values'])
        panel.model.bags=copy.deepcopy(item.payload['bags'])
        panel.model.rng=clone_rng(item.payload['rng'])
        for key,value in panel.model.values.items(): panel.values[key].set(value)
        if panel.model.render_style=='近景摄影':
            from scene_tool.ui.studio_binding import sync_scene_studio
            sync_scene_studio(panel, preserve_values=True)
        panel.updating=False
        panel.model.prompt=panel.model.rendered=item.prompt
        panel.model.undo=None
        panel.show_prompt()
        panel.persist()
        return True
    show_variants(panel,candidates,apply)

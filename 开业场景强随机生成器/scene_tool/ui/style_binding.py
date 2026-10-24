"""Bind the current industry's real dimensions, candidates and copy to the UI."""
from scene_tool.domain.industry_profiles import industry_pools, dimensions, industry_key
from scene_tool.ui.camera_binding import sync_opening_camera


def sync_style(view, replace=False):
    style, industry = view.render_style.get(), view.industry.get()
    environment = view.values['environment'].get()
    if getattr(view, 'parameter_style', style) != style:
        from scene_tool.ui.parameter_panel import build_parameters
        build_parameters(view, view.parameter_host)
    context = (industry_key(industry), environment, style)
    previous_context = getattr(view, 'industry_context', None)
    changed = previous_context != context
    view.industry_context = context
    pools = view.engine.scoped_pools(industry, environment, style)
    for key, label in dimensions(style):
        if key == 'architecture' and environment == '室内' and style != '商业效果图':
            label = '内部装潢风格'
        view.parameter_labels[key].configure(text=label)
        if key in pools:
            pool = pools[key]
            view.combos[key].configure(values=pool)
            if (changed or replace) and view.values[key].get() not in pool:
                view.values[key].set(view.engine.rng.choice(pool))
    sync_opening_camera(view)
    if changed and (previous_context is None or previous_context[0] != context[0]) and not (previous_context is None and view.copy_locked.get()):
        view.copyline.set(view.copy_engine.draw(view.copyline.get(), True, False, industry))


def environment_changed(view, *_):
    if view.ready:
        view.ready = False
        sync_style(view, replace=True)
        view.ready = True
        view.schedule_refresh()

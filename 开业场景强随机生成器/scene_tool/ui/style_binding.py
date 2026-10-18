"""Keep the visible style field and its candidate pool aligned with the scene."""


def sync_style(view, replace=False):
    indoor = view.values['environment'].get() == '室内'
    key = 'interior' if indoor else 'architecture'
    other = 'architecture' if indoor else 'interior'
    label = '内部装潢风格' if indoor else '门店建筑风格'
    view.parameter_labels['architecture'].configure(text=f'06  {label}')
    view.combos['architecture'].configure(values=view.engine.pools[key])
    current = view.values['architecture'].get()
    if replace or current in view.engine.pools[other]:
        view.values['architecture'].set(view.engine.pools[key][0])


def environment_changed(view, *_):
    if view.ready:
        sync_style(view, replace=True)
        view.schedule_refresh()

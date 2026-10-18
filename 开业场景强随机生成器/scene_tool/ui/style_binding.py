"""Keep the visible style field and its candidate pool aligned with the scene."""


from scene_tool.storage.pools import retired_balloon_values


def sync_style(view, replace=False):
    indoor = view.values['environment'].get() == '室内'
    for field, indoor_key, row, inside_label, outside_label in (
        ('architecture', 'interior', 6, '内部装潢风格', '门店建筑风格'),
        ('placement', 'indoor_placement', 7, '室内KT板布置位置', '室外KT板布置位置'),
        ('balloons', 'indoor_balloons', 8, '室内气球造型', '室外气球造型'),
    ):
        key, other = (indoor_key, field) if indoor else (field, indoor_key)
        label = inside_label if indoor else outside_label
        view.parameter_labels[field].configure(text=label)
        if field in view.combos:
            view.combos[field].configure(values=view.engine.pools[key])
        current = view.values[field].get()
        retired = field == 'balloons' and current in retired_balloon_values() and current not in view.engine.pools[key]
        if replace or current in view.engine.pools[other] or retired:
            view.values[field].set(view.engine.pools[key][0])


def environment_changed(view, *_):
    if view.ready:
        sync_style(view, replace=True)
        view.schedule_refresh()

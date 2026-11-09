"""Rotate secondary groups while drawing major changes through the existing engines."""
from scene_tool.config.closeup import CLOSEUP
from scene_tool.config.appearance_rules import static_keys
from scene_tool.config.random_strategy import PRIMARY, CLOSE_MAIN, CLOSE_GROUPS, OPEN_MAIN, OPEN_GROUPS
from scene_tool.domain.industry_profiles import dimensions
from scene_tool.generation.lock_policy import contextual_locks


def active_keys(values, locked, hidden, main, groups, step):
    available = set(values) - set(locked) - set(hidden)
    eligible = [set(group) & available for group in groups if set(group) & available]
    selected = set(main) & available
    if eligible:
        selected.update(eligible[step % len(eligible)])
    # Never strand an empty field when starting from an incomplete manual edit.
    selected.update(k for k in available if not values.get(k))
    if set(CLOSE_MAIN) & selected:
        selected.update(set(CLOSE_MAIN) & set(values) - set(locked))
    if {'detail_reflection','detail_light'} & selected:
        selected.update({'detail_reflection','detail_light'} & set(values) - set(locked))
    return selected


def draw_opening(engine, current, locks, *, strategy, hidden, strong, style, industry,
                 step=0, copy_random=True, copy_locked=False):
    if strategy != PRIMARY:
        return engine.draw(current, locks, strong, style, industry), copy_random and not copy_locked
    values = {k:current.get(k,'') for k,_ in dimensions(style)}
    locked = set(locks)
    if style == CLOSEUP:
        locked.update(static_keys(engine.scoped_pools(industry,current.get('environment'),style),current))
    if style != CLOSEUP:
        locked = contextual_locks(current,locked,style)
        values['copy'] = 'current copy'
        if copy_locked or not copy_random: locked.add('copy')
    main, groups = (CLOSE_MAIN,CLOSE_GROUPS) if style == CLOSEUP else (OPEN_MAIN,OPEN_GROUPS)
    selected = active_keys(values, locked, hidden, main, groups, step)
    temporary = locked | (set(values) - selected)
    result = engine.draw(current, temporary, strong, style, industry, preserve_locked=True)
    return result, 'copy' in selected


def draw_scene(model, step=0):
    if model.random_strategy != PRIMARY:
        model.draw()
        return
    mapping = {d['key']:d.get('close_key',d['key']) for d in model.active_profile()['dimensions']}
    values = {mapping[k]:v for k,v in model.values.items() if k in mapping}
    locks = {mapping[k] for k,v in model.locks.items() if v and k in mapping}
    hidden = {mapping[k] for k,v in model.hidden.items() if v and k in mapping}
    if model.render_style == CLOSEUP:
        pools = {mapping[k]:v for k,v in model.active_pools().items()}
        locks.update(static_keys(pools,values))
        main,groups = CLOSE_MAIN,CLOSE_GROUPS
    else:
        keys = [d['key'] for d in model.active_profile()['dimensions']]
        main = (keys[0],keys[2],keys[5],'camera')
        groups = ((keys[1],keys[3]),(keys[4],keys[6]),('time',),('ratio',))
    selected = active_keys(values,locks,hidden,main,groups,step)
    original = model.locks
    model.locks = {k: original.get(k,False) or mapping.get(k,k) not in selected for k in model.values}
    try:
        model.draw(preserve_locked=True)
    finally:
        model.locks = original


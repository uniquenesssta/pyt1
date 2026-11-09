"""Filter, reconcile and validate reflection using a user-selected surface finish."""
from scene_tool.config import material_finish as finish, surface_reflection as surf, highlight_position as light

def compatible(value, strength, position=None):
    value=finish.normalize(value)
    strength=surf.normalize(strength)
    if value==finish.FOLLOW: return True
    if strength not in finish.ALLOWED[value]: return False
    return position is None or (position in light.OPTIONS and light.compatible(finish.effective(value,strength),position))

def message(value):
    return f'材质表面为“{value}”，与反光或亮光位置不符。请调整表面属性，或解锁冲突项。'

def filter_pools(pools, value, current, locked):
    value=finish.normalize(value)
    if value==finish.FOLLOW: return pools
    strength=surf.normalize(current.get(surf.KEY))
    if surf.KEY in locked and strength and not compatible(value,strength):
        raise ValueError(message(value))
    result={k:list(v) for k,v in pools.items()}
    result[surf.KEY]=[s for s in result[surf.KEY] if compatible(value,s)]
    if not result[surf.KEY]: raise ValueError('反光候选池中没有符合材质表面的选项，请调整候选池或材质表面。')
    return result

def validate(values, hidden=(), light_key=light.KEY):
    value=finish.normalize(values.get(finish.KEY))
    if value==finish.FOLLOW: return
    strength=surf.normalize(values.get(surf.KEY,surf.AUTO)) if surf.KEY not in hidden else surf.AUTO
    position=values.get(light_key) if light_key not in hidden else None
    if not compatible(value,strength,position): raise ValueError(message(value))

def reconcile(values, locks, value, light_key=light.KEY):
    value=finish.normalize(value)
    result=dict(values)
    result[finish.KEY]=value
    if value==finish.FOLLOW: return result
    old_s=surf.normalize(values.get(surf.KEY,surf.AUTO))
    old_p=values.get(light_key,light.NONE)
    strengths=list(dict.fromkeys([old_s,value,surf.AUTO,*surf.OPTIONS]))
    positions=list(dict.fromkeys([old_p,light.NONE,light.CENTER,*light.OPTIONS]))
    for s in strengths:
        for p in positions:
            if surf.KEY in locks and s!=old_s: continue
            if light_key in locks and p!=old_p: continue
            if compatible(value,s,p):
                result[surf.KEY],result[light_key]=s,p
                return result
    raise ValueError(message(value))


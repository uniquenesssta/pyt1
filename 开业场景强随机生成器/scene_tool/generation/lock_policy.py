"""Keep location-dependent locks in their existing indoor/outdoor context."""
def contextual_locks(current, locked, style=None):
    locked = set(locked)
    dependent={'architecture','placement','balloons'}
    if style != '商业效果图': dependent.add('camera')
    if current.get('environment') and any(current.get(k) for k in
        locked.intersection(dependent)):
        locked.add('environment')
    return locked

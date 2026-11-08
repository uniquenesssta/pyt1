"""Main changes and secondary groups, separate from the shuffle strength setting."""
PRIMARY = '主变化优先'
ALL = '全部随机'
STRATEGIES = (PRIMARY, ALL)

def normalize(value):
    return value if value in STRATEGIES else PRIMARY

CLOSE_MAIN = ('camera', 'detail_crop', 'detail_focus', 'detail_plane')
CLOSE_GROUPS = (('detail_edge', 'detail_space'), ('detail_layers',),
                ('detail_surface', 'detail_art'), ('detail_reflection', 'detail_light'), ('ratio',))
OPEN_MAIN = ('environment', 'architecture', 'placement', 'balloons', 'camera', 'display_space', 'background_depth')
OPEN_GROUPS = (('city', 'address'), ('brand', 'logo_shape', 'logo_structure', 'copy'), ('lighting',), ('ratio',))


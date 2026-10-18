"""Resolve the active candidate pool for environment-dependent dimensions."""
INDOOR_KEYS = {'architecture': 'interior', 'placement': 'indoor_placement', 'balloons': 'indoor_balloons'}
EXTRA_LABELS = (('interior', '内部装潢风格'), ('indoor_placement', '室内KT板布置位置'),
                ('indoor_balloons', '室内气球造型'))


def pool_key(key, environment):
    return INDOOR_KEYS.get(key, key) if environment == '室内' else key

"""Scene catalogs and per-mode persistence, separate from commercial settings."""
from scene_tool.config.paths import RESOURCES, DATA
from scene_tool.storage.json_files import load_json, atomic_json

SCENE_IDS = ('hotel_entrance', 'hotel_lobby', 'private_room', 'apartment', 'villa', 'lawn_wedding', 'residential')


def load_profiles():
    profiles = [load_json(RESOURCES / 'scenes' / (key + '.json')) for key in SCENE_IDS]
    legacy = load_json(RESOURCES / 'legacy_scene_pools_v1.json')
    for profile in profiles:
        profile['legacy_pools'] = legacy.get(profile['id'], {})
    return profiles


def load_scene_states():
    path = DATA / 'scene_modes.json'
    if not path.exists():
        return {'active': '开业场景', 'scenes': {}}
    result = load_json(path)
    if not isinstance(result, dict) or not isinstance(result.get('scenes', {}), dict):
        raise ValueError('场景设置格式错误')
    return result


def save_scene_states(active, models):
    atomic_json(DATA / 'scene_modes.json', {'active': active, 'scenes': {k: m.state() for k, m in models.items()}})

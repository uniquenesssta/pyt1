"""Scene catalogs and per-mode persistence, separate from commercial settings."""
from scene_tool.config.paths import RESOURCES, DATA
from scene_tool.storage.json_files import load_json
from scene_tool.storage.scene_sessions import load_states, save_states

SCENE_IDS = ('hotel_entrance', 'hotel_lobby', 'private_room', 'apartment', 'villa', 'lawn_wedding', 'residential')


def load_profiles():
    profiles = [load_json(RESOURCES / 'scenes' / (key + '.json')) for key in SCENE_IDS]
    legacy = load_json(RESOURCES / 'legacy_scene_pools_v1.json')
    cameras = load_json(RESOURCES / 'legacy_scene_camera_v2.json')
    for profile in profiles:
        profile['legacy_camera'] = cameras.get(profile['id'], [])
        profile['legacy_pools'] = legacy.get(profile['id'], {})
    return profiles


def load_scene_states():
    return load_states(DATA, load_profiles())


def save_scene_states(active, models):
    save_states(DATA, active, models)


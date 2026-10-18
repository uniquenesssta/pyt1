"""Per-scene atomic sessions with migration from the combined legacy file."""
from scene_tool.storage.json_files import load_json, atomic_json
from scene_tool.storage.scene_codec import encode_scene, decode_scene


def load_states(directory, profiles):
    index = directory / 'scene_modes.json'
    result = load_json(index) if index.exists() else {}
    if not isinstance(result, dict) or not isinstance(result.get('scenes', {}), dict):
        raise ValueError('场景设置格式错误')
    states = dict(result.get('scenes', {}))
    errors = []
    for profile in profiles:
        path = directory / 'scenes' / (profile['id'] + '.json')
        if path.exists():
            try:
                states[profile['name']] = decode_scene(profile, load_json(path))
            except (OSError, ValueError, TypeError, AttributeError, KeyError) as exc:
                errors.append(f"{profile['name']}读取失败：{exc}")
    return {'active': result.get('active', '开业场景'), 'scenes': states, 'errors': errors}


def write_changed(path, value):
    try:
        if path.exists() and load_json(path) == value:
            return
    except (OSError, ValueError):
        pass
    atomic_json(path, value)


def save_states(directory, active, models):
    # Write every scene successfully before replacing the legacy combined index.
    for model in models.values():
        write_changed(directory / 'scenes' / (model.profile['id'] + '.json'), encode_scene(model))
    write_changed(directory / 'scene_modes.json', {'version': 2, 'active': active})

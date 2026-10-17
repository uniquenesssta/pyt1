from scene_tool.storage.json_files import load_json, atomic_json


def load_session(path):
    state = load_json(path)
    if not isinstance(state, dict):
        raise ValueError('设置应为对象')
    for section in ('values', 'locks'):
        if not isinstance(state.get(section, {}), dict):
            raise ValueError(f'{section} 格式错误')
    return state


def save_session(path, state):
    atomic_json(path, state)

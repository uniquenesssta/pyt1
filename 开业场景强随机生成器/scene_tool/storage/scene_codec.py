"""Compact disk representation; runtime models continue using complete text."""
import hashlib
import json


def pool_digest(pool):
    return hashlib.sha256(json.dumps(pool, ensure_ascii=False).encode('utf-8')).hexdigest()


def encode_scene(model):
    state = dict(model.state())
    defaults = {d['key']: d['options'] for d in model.profile['dimensions']}
    state['pools'] = {k: v for k, v in model.pools.items() if v != defaults[k]}
    state['camera_mode_bags'] = {k: v for k, v in model.bags.items() if k.startswith('camera_mode:')}
    state['bags'] = {}
    for key, pool in model.pools.items():
        indices = {value: i for i, value in enumerate(pool)}
        state['bags'][key] = {'pool_hash': pool_digest(pool),
                              'indices': [indices[x] for x in model.bags[key] if x in indices]}
    if state['prompt'] == state['rendered']:
        del state['rendered']
    state['version'] = 2
    return state


def decode_scene(profile, saved):
    if not isinstance(saved, dict):
        raise ValueError('场景设置必须是对象')
    if saved.get('version') != 2:
        return saved
    state = dict(saved)
    defaults = {d['key']: d['options'] for d in profile['dimensions']}
    overrides = state.get('pools', {})
    state['bags'] = {}
    for key, default in defaults.items():
        pool = overrides.get(key, default)
        bag = saved.get('bags', {}).get(key, {})
        state['bags'][key] = [pool[i] for i in bag.get('indices', [])
                              if type(i) is int and 0 <= i < len(pool)] if bag.get('pool_hash') == pool_digest(pool) else []
    state.setdefault('rendered', state.get('prompt', ''))
    return state


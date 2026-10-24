from scene_tool.config.paths import RESOURCES
from scene_tool.domain.pools import validate_pools, upgrade_pools
from scene_tool.storage.json_files import load_json, atomic_json


def load_pools(path):
    return validate_pools(load_json(path))


def load_startup_pools(custom_path):
    defaults = load_pools(RESOURCES / 'pools.json')
    errors = []
    try:
        pools = load_pools(custom_path) if custom_path.exists() else defaults
    except (OSError, ValueError) as exc:
        pools = defaults
        errors.append(f'自定义参数池无法读取，已使用默认池。\n{exc}')
    for name in ('legacy_pools_v1.json', 'legacy_pools_v2.json', 'legacy_pools_v3.json', 'legacy_pools_v4.json'):
        pools = upgrade_pools(pools, defaults, load_json(RESOURCES / name))
    return pools, errors


def save_pools(path, pools):
    atomic_json(path, validate_pools(pools))


def retired_balloon_values():
    return load_json(RESOURCES / 'legacy_pools_v3.json')['balloons']


from scene_tool.generation.brands import generate_brand
from scene_tool.generation.addresses import generate_address

def fresh_value(key, rng, previous, recent):
    factory = generate_brand if key == 'brand' else generate_address
    excluded = set(recent)
    excluded.add(previous)
    for _ in range(1000):
        value = factory(rng)
        if value not in excluded:
            return value
    raise ValueError('暂未抽到新组合，请重试。')

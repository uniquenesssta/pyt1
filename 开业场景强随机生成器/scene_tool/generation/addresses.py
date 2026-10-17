from scene_tool.config.vocabulary import STREET_FIRST, STREET_SECOND, STREET_TYPES

def generate_address(rng):
    return f'{rng.choice(STREET_FIRST)}{rng.choice(STREET_SECOND)}{rng.choice(STREET_TYPES)} {rng.randint(1, 999)} 号'

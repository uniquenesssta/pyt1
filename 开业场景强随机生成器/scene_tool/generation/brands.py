from scene_tool.config.vocabulary import SYLLABLES

def brand_from_parts(parts):
    """Use the same sampled syllables for both scripts; never draw them separately."""
    return ''.join(western for western, _ in parts) + ' ' + ''.join(chinese for _, chinese in parts)

def generate_brand(rng):
    # Two or three distinct syllables, each with a fixed Chinese reading.
    return brand_from_parts(rng.sample(SYLLABLES, rng.choice((2, 3))))

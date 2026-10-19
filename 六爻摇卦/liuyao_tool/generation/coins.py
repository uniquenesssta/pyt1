"""三枚独立、等概率的铜钱，每枚取值 2 或 3。"""
import random

from ..domain.yao import YAO_TYPES


def toss_line(rng=None):
    source = rng if rng is not None else random.SystemRandom()
    return YAO_TYPES[sum(source.choice((2, 3)) for _ in range(3))]

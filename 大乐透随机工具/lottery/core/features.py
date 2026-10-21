"""各原脚本统一采用排序后的前区和五个七号码分区。"""
from dataclasses import dataclass


def zone(number):
    return (number - 1) // 7 + 1


@dataclass(frozen=True)
class Features:
    gaps: tuple[int, ...]
    max_span: int
    start_span: int
    longest_run: int
    empty_zones: tuple[int, ...]
    intermediate_zones: tuple[int, ...]


def features(front):
    nums = sorted(front)
    gaps = tuple(b - a for a, b in zip(nums, nums[1:]))
    spans = [zone(b) - zone(a) for a, b in zip(nums, nums[1:]) if b - a > 7]
    intermediate = set()
    for a, b in zip(nums, nums[1:]):
        if b - a > 10:
            intermediate.update(range(zone(a) + 1, zone(b)))
    longest = run = 1
    for gap in gaps:
        run = run + 1 if gap == 1 else 1
        longest = max(longest, run)
    occupied = {zone(n) for n in nums}
    return Features(gaps, max(spans, default=0), zone(nums[0]) - 1,
                    longest, tuple(z for z in range(1, 6) if z not in occupied),
                    tuple(sorted(intermediate)))

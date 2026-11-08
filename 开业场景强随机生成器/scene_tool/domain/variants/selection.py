"""Select visibly different candidates without inventing additional results."""
from dataclasses import dataclass

@dataclass
class Variant:
    prompt: str
    features: dict
    payload: object


def select_variants(candidates, limit=4):
    unique = {}
    prompts = set()
    for candidate in candidates:
        signature = tuple(candidate.features.items())
        if signature not in unique and candidate.prompt not in prompts:
            unique[signature] = candidate
            prompts.add(candidate.prompt)
    remaining = list(unique.values())
    if not remaining:
        return []
    selected = [remaining.pop(0)]
    weights = {'镜头类别': 12, '机位': 5, '构图': 6, '空间': 4, '摆位': 4, '光线': 3}
    def distance(a,b):
        return sum(weights.get(k, 1) for k,v in a.features.items() if b.features.get(k) != v)
    while remaining and len(selected) < limit:
        best = max(remaining, key=lambda c: min(distance(c, chosen) for chosen in selected))
        remaining.remove(best)
        selected.append(best)
    return selected

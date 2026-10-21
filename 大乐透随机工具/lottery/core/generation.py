"""系统随机源、组合空间校验、去重和可取消批量生成。"""
from dataclasses import dataclass
from itertools import combinations
from math import comb, isfinite
from random import SystemRandom
from .models import Ticket, validate_numbers, check_cancel
from .weighted import StructurePool, weighted_sample

MODES = ("均匀随机", "历史频率加权", "历史结构加权")


@dataclass(frozen=True)
class GenerationConfig:
    count: int = 1
    front_count: int = 5
    back_count: int = 2
    front_fixed: tuple = ()
    back_fixed: tuple = ()
    front_excluded: tuple = ()
    back_excluded: tuple = ()
    mode: str = MODES[0]
    unique: bool = True
    max_span_weights: tuple = ()
    start_span_weights: tuple = ()
    structure_profile: object = None

    def validate(self):
        if type(self.count) is not int or not 1 <= self.count <= 10000:
            raise ValueError("每批生成组数须为 1–10000")
        if self.mode not in MODES:
            raise ValueError("未知随机模式")
        for name, maximum, minimum, count, fixed, excluded in [
            ("前区", 35, 5, self.front_count, self.front_fixed, self.front_excluded),
            ("后区", 12, 2, self.back_count, self.back_fixed, self.back_excluded),
        ]:
            if type(count) is not int or not minimum <= count <= maximum:
                raise ValueError(f"{name}数量须为 {minimum}–{maximum}")
            validate_numbers(fixed, maximum, 0, count, name + "固定")
            validate_numbers(excluded, maximum, 0, maximum, name + "排除")
            if set(fixed) & set(excluded):
                raise ValueError(f"{name}固定和排除号码不能重叠")
            if maximum - len(excluded) < count:
                raise ValueError(f"{name}排除后可用号码不足")
        for weights in (self.max_span_weights, self.start_span_weights):
            if weights and (len(weights) != 5 or any(not isfinite(w) or w < 0 or w > 100 for w in weights) or not any(weights)):
                raise ValueError("跨区权重须为 5 个 0–100 数值，且不能全为 0")
        if self.mode == MODES[2] and self.front_count != 5:
            raise ValueError("历史结构加权仅适用于前区 5 个号码；复式请选择均匀或历史频率加权")
        if self.mode != MODES[2] and (self.max_span_weights or self.start_span_weights):
            raise ValueError("自定义跨区权重仅用于历史结构加权模式")


def unrank_combination(pool, count, rank):
    """按字典序还原组合；不必创建巨大的组合列表。"""
    result = []
    start = 0
    for remaining in range(count, 0, -1):
        for index in range(start, len(pool) - remaining + 1):
            block = comb(len(pool) - index - 1, remaining - 1)
            if rank < block:
                result.append(pool[index])
                start = index + 1
                break
            rank -= block
    return tuple(result)


def generate(config, stats=None, cancel=None, progress=None, rng=None):
    config.validate()
    from .cross_weights import resolve_cross_overrides
    config = resolve_cross_overrides(config)
    if config.structure_profile is not None and config.mode != MODES[0]:
        config.structure_profile.validate()
        stats = config.structure_profile.stats
    check_cancel(cancel)
    rng = rng if rng is not None else SystemRandom()
    front_pool = tuple(n for n in range(1, 36) if n not in config.front_fixed and n not in config.front_excluded)
    back_pool = tuple(n for n in range(1, 13) if n not in config.back_fixed and n not in config.back_excluded)
    nf, nb = config.front_count - len(config.front_fixed), config.back_count - len(config.back_fixed)
    front_size, back_size = comb(len(front_pool), nf), comb(len(back_pool), nb)
    capacity = front_size * back_size
    if config.unique and config.count > capacity:
        raise ValueError(f"当前条件最多 {capacity:,} 组不重复号码，请减少组数或取消批内去重")
    if config.mode == MODES[0]:
        ranks = rng.sample(range(capacity), config.count) if config.unique else [rng.randrange(capacity) for _ in range(config.count)]
        results = []
        for i, rank in enumerate(ranks):
            if i % 100 == 0:
                check_cancel(cancel)
                if progress:
                    progress(f"已生成 {i:,} / {config.count:,} 组")
            f, b = divmod(rank, back_size)
            results.append(Ticket(config.front_fixed + unrank_combination(front_pool, nf, f),
                                  config.back_fixed + unrank_combination(back_pool, nb, b)))
        check_cancel(cancel)
        return results
    if stats is None or stats.total == 0:
        raise ValueError("历史加权需要先导入有效历史数据")
    front_weights = {n: stats.front[n] + 1 for n in range(1, 36)}
    back_weights = {n: stats.back[n] + 1 for n in range(1, 13)}
    structure = StructurePool(config, stats, cancel, progress) if config.mode == MODES[2] else None
    if structure:
        capacity = len(structure.fronts) * back_size
        if config.unique and config.count > capacity:
            raise ValueError(f"跨区限制后最多 {capacity:,} 组不重复号码")
    results, seen = [], set()
    # 较小候选空间全量求权重并无放回抽样，避免快抽满时反复碰撞。
    if config.unique and capacity <= 50000:
        fronts = structure.fronts if structure else [tuple(sorted(config.front_fixed + f)) for f in combinations(front_pool, nf)]
        backs = [tuple(sorted(config.back_fixed + b)) for b in combinations(back_pool, nb)]
        from .selection import select_small_space
        return select_small_space(fronts, backs, config, front_weights, back_weights, structure, rng, cancel)
    limit = max(20000, config.count * 200)
    for attempt in range(limit):
        if attempt % 100 == 0:
            check_cancel(cancel)
            if progress:
                progress(f"已生成 {len(results):,} / {config.count:,} 组")
        front = structure.choose(rng) if structure else config.front_fixed + tuple(weighted_sample(front_pool, nf, front_weights, rng))
        back = config.back_fixed + tuple(weighted_sample(back_pool, nb, back_weights, rng))
        ticket = Ticket(front, back)
        if config.unique and ticket in seen:
            continue
        seen.add(ticket)
        results.append(ticket)
        if len(results) == config.count:
            check_cancel(cancel)
            return results
    raise ValueError(f"权重过于集中，仅找到 {len(results)} 组不同号码；请减少组数、取消去重或使用均匀随机。未替换上次结果。")

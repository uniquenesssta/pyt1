"""单窗口内的单条候选缓存；不保存随机数、抽样结果或半成品。"""
from bisect import bisect_right
from dataclasses import asdict, dataclass
from hashlib import sha256
from threading import Lock
from .models import check_cancel
from .weighted import StructurePool


def freeze(value):
    if isinstance(value, dict):
        return tuple(sorted(((freeze(k), freeze(v)) for k, v in value.items()), key=repr))
    if isinstance(value, (list, tuple)):
        return tuple(freeze(v) for v in value)
    return value


def cache_key(config, stats):
    profile = config.structure_profile
    history = None if profile is None else (
        profile.requested,
        tuple((d.issue, d.ticket.front, d.ticket.back) for d in profile.draws),
        freeze(profile.weights), freeze(profile.strengths))
    # 不纳入批量组数、去重开关和后区条件：它们不改变前区候选及评分。
    data = (config.front_count, tuple(sorted(config.front_fixed)),
            tuple(sorted(config.front_excluded)), config.max_span_weights,
            config.start_span_weights, freeze(asdict(stats)), history)
    return sha256(repr(data).encode('utf-8')).digest()


@dataclass(frozen=True)
class CachedPool:
    fronts: tuple
    cumulative: tuple

    def choose(self, rng):
        index = bisect_right(self.cumulative, rng.random() * self.cumulative[-1])
        return self.fronts[min(index, len(self.fronts)-1)]


class StructureCache:
    def __init__(self):
        self._lock = Lock()
        self._key, self._pool = None, None
        self._epoch = 0
        self.hits, self.builds = 0, 0

    def clear(self):
        with self._lock:
            self._key, self._pool = None, None
            self._epoch += 1

    def get(self, config, stats, cancel=None, progress=None):
        check_cancel(cancel)
        key = cache_key(config, stats)
        check_cancel(cancel)
        with self._lock:
            epoch = self._epoch
            pool = self._pool if key == self._key else None
            if pool is not None:
                self.hits += 1
        if pool is not None:
            if progress:
                progress(f'复用结构候选缓存：{len(pool.fronts):,} 个组合，正在重新随机抽取')
            check_cancel(cancel)
            return pool
        built = StructurePool(config, stats, cancel, progress)
        check_cancel(cancel)
        pool = CachedPool(tuple(built.fronts), tuple(built.cumulative))
        with self._lock:
            check_cancel(cancel)
            if epoch == self._epoch:
                self._key, self._pool = key, pool
                self.builds += 1
        return pool

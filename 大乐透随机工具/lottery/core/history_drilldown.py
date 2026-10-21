"""统计条目回查：匹配具体开奖记录并保留每期贡献次数。"""
from dataclasses import dataclass
from .features import features, zone
from .structure_profile import structure_values
from .history_window import select_window
from .querying import search
from .models import check_cancel


@dataclass(frozen=True)
class StatisticFilter:
    source: str
    category: str
    item: str

    @property
    def label(self):
        return f'{self.category} · {self.item}'

    def contribution(self, draw):
        category, item = self.category, self.item
        if self.source == '结构权重':
            values = structure_values(draw.ticket.front)
            if category not in values: raise ValueError('未知结构指标')
            return int(str(values[category]) == item)
        if category.startswith(('前区·','后区·')):
            numbers = draw.ticket.front if category.startswith('前区') else draw.ticket.back
            return int(int(item) in numbers)
        if category == '后区组合':
            return int(draw.ticket.back == tuple(map(int,item.split())))
        f = features(draw.ticket.front)
        if category == '分区号码频率':
            return sum(zone(n) == int(item.split('区')[0]) for n in draw.ticket.front)
        if category == '空区': return int(int(item.split('区')[0]) in f.empty_zones)
        if category == '差值>10覆盖中间区': return int(int(item.split('区')[0]) in f.intermediate_zones)
        if category == '最大跨区·相邻差>7': return int(f.max_span == int(item))
        if category == '起始隐含跨区': return int(f.start_span == int(item))
        if category == '最长连号·互斥': return int(f.longest_run == int(item))
        if category == '至少N连号·可重叠': return int(f.longest_run >= int(item))
        if category in tuple(f'C{i}相邻差值' for i in range(1,5)):
            return int(f.gaps[int(category[1])-1] == int(item))
        raise ValueError('未知统计指标，无法回查')


def query_history(draws, query, periods=0, statistic=None, cancel=None):
    check_cancel(cancel)
    if periods or (statistic and statistic.source == '结构权重'):
        selected, order = select_window(draws, periods)
    else:
        selected, order = list(draws), '全部导入记录（保留原统计重复行）'
    rows = search(selected, query, cancel)
    if statistic is None:
        return rows, len(selected), len(rows), order
    matched, contributions = [], 0
    for index, (draw, detail) in enumerate(rows):
        if index % 256 == 0: check_cancel(cancel)
        count = statistic.contribution(draw)
        if count:
            contributions += count
            note = f'{statistic.label}；本期贡献 {count} 次'
            matched.append((draw, note + ('；'+detail if detail else '')))
    check_cancel(cancel)
    return matched, len(selected), contributions, order

"""结构页和选号主页按同一套分组展示指标。"""
from ..core.temporal_indicators import TEMPORAL_INDICATORS
from ..core.trend_indicators import BACK, FRONT, TREND_INDICATORS


GROUPS = {
    '差值': tuple(f'C{i}差值' for i in range(1, 5)),
    '连号': ('连号形态', '最长连号'),
    '空区': ('空区数量',) + tuple(f'{z}区空区' for z in range(1, 6)),
    '跨区': ('最大跨区（差值>7）', '起始跨区'),
    '中间覆盖': tuple(f'{z}区中间覆盖（差值>10）' for z in range(1, 6)),
    '前区形态': ('前区奇偶比', '前区小大比', '前区012路比', '前区质合比', '前区同尾组数'),
    '前区数值': ('前区和值', '前区跨度', '前区AC值'),
    '前区区间': ('前区三区比', '前区五区比'),
    '后区结构': tuple(name for name, indicator in TREND_INDICATORS.items()
                       if indicator.zone == BACK and not indicator.position),
    '跨期重邻孤': tuple(name for name, indicator in TEMPORAL_INDICATORS.items() if not indicator.parts),
    '遗漏结构': ('前区遗漏结构', '后区遗漏结构'),
    '前区定位': tuple(name for name, indicator in TREND_INDICATORS.items()
                       if indicator.zone == FRONT and indicator.position),
    '后区定位': tuple(name for name, indicator in TREND_INDICATORS.items()
                       if indicator.zone == BACK and indicator.position),
}

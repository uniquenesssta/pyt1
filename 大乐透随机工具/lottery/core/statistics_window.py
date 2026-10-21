"""普通统计的范围选择；全量保留导入记录，近期按期号去重。"""
from .history_window import select_window
from .statistics import analyze


def window_statistics(draws, periods=0):
    if periods not in (0, 50, 100):
        raise ValueError('统计范围请选择近50期、近100期或全部')
    if not draws:
        return analyze([]), '暂无历史数据'
    if periods:
        selected, order = select_window(draws, periods)
    else:
        selected, order = list(draws), '全部导入记录（保留原统计重复行）'
    if all(d.issue for d in selected):
        first = min(selected, key=lambda d:int(d.issue)).issue
        last = max(selected, key=lambda d:int(d.issue)).issue
        extent = f'{first}–{last}'
    else:
        extent = '无完整期号'
    stats = analyze(selected)
    return stats, f'实际 {len(selected):,} 条 · {extent} · {order}'

"""按期号选择最近 N 期；无期号时明确按文件顺序。"""
from .draw_index import issue_key


def ordered_history(draws):
    if not draws:
        raise ValueError('请先导入历史数据')
    has_issue = [bool(d.issue) for d in draws]
    if any(has_issue) and not all(has_issue):
        raise ValueError('期号不完整，无法确定最近期数，请补全期号')
    if all(has_issue):
        unique = {}
        for d in draws:
            key = int(issue_key(d.issue))
            previous = unique.get(key)
            if previous is not None:
                if previous.ticket != d.ticket:
                    raise ValueError(f'第 {d.issue} 期有不同号码，请先核对')
                if previous.draw_date and d.draw_date and previous.draw_date != d.draw_date:
                    raise ValueError(f'第 {d.issue} 期有不同开奖日期，请先核对')
            if previous is None or d.draw_date or not previous.draw_date:
                unique[key] = d
        ordered = [unique[k] for k in sorted(unique)]
        order = '按期号排序并按期去重'
    else:
        ordered = list(draws)
        order = '无期号，按文件顺序取末尾记录'
    return ordered, order


def window_start(ordered, periods):
    if type(periods) is not int or periods < 0:
        raise ValueError('统计期数须为正整数；0 表示全部')
    return max(0, len(ordered) - periods) if periods else 0


def select_window(draws, periods=50):
    ordered, order = ordered_history(draws)
    return ordered[window_start(ordered, periods):], order

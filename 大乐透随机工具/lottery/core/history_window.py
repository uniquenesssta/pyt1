"""按期号选择最近 N 期；无期号时明确按文件顺序。"""

def select_window(draws, periods=50):
    if type(periods) is not int or periods < 0:
        raise ValueError('统计期数须为正整数；0 表示全部')
    if not draws:
        raise ValueError('请先导入历史数据')
    has_issue = [bool(d.issue) for d in draws]
    if any(has_issue) and not all(has_issue):
        raise ValueError('期号不完整，无法确定最近期数，请补全期号')
    if all(has_issue):
        unique = {}
        for d in draws:
            key = int(d.issue)
            if key in unique and unique[key].ticket != d.ticket:
                raise ValueError(f'第 {d.issue} 期有不同号码，请先核对')
            unique[key] = d
        ordered = [unique[k] for k in sorted(unique)]
        order = '按期号排序并按期去重'
    else:
        ordered = list(draws)
        order = '无期号，按文件顺序取末尾记录'
    selected = ordered[-periods:] if periods else ordered
    return selected, order

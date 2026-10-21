"""统计跳转与历史筛选任务协调，保留同一数据集口径。"""
from ..core.history_drilldown import StatisticFilter, query_history


def search_history(app):
    if app.dataset is None:
        app.set_status('请先导入历史数据'); return
    try:
        query = app.history.snapshot()
        periods = app.history.periods()
    except ValueError as exc:
        app.error(exc); return
    statistic = app.history.statistic
    draws = app.dataset.draws
    def work(cancel, progress):
        return query_history(draws, query, periods, statistic, cancel)
    def done(value):
        rows,total,counts,order = value
        app.history.set_results(rows,total)
        note = f'实际范围 {total:,} 条 · 匹配 {len(rows):,} 条 · {order}'
        if rows and all(draw.issue for draw, _ in rows):
            note += f' · 不同期号 {len({int(draw.issue) for draw, _ in rows}):,} 期'
        if statistic:
            note += f' · 对应统计次数 {counts:,}'
        app.history.caption.configure(text=note)
        app.set_status('查询完成：'+note)
    app.jobs.start(work, done, app.error)


def open_statistic(app, source, category, item):
    if app.jobs.running:
        app.set_status('请等待当前任务完成再查看统计明细'); return
    if app.dataset is None: return
    periods = 0
    if source == '结构权重':
        # 使用实际展示的统计快照；未提交的输入不能改变双击行的来源。
        profile = app.structure_weights.profile
        if profile is None: return
        periods = profile.requested
    app.history.statistic = StatisticFilter(source, category, str(item))
    app.history.period.set(str(periods) if periods else '全部')
    app.history.text.set('')
    app.history.condition.set(f'统计条件：{category} · {item}（可叠加号码/期号与期数筛选）')
    app.tabs.select(app.history)
    search_history(app)

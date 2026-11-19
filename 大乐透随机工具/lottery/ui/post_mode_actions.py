"""从当前历史取数，把统计和选号交给后台任务。"""
from ..core.calendar_generation import generate_calendar_set
from ..core.calendar_samples import CALENDAR_MODE, select_calendar_samples
from ..core.conditional_frequency import analyze_conditional_frequency, conditional_weights
from ..core.generation import generate


def _draws(app):
    if app.dataset is None:
        raise ValueError("请先导入历史或更新开奖数据")
    return tuple(app.dataset.draws)


def _show_tickets(app, tickets, *, calendar=False):
    app.generated.set_tickets(tickets, label_sizes=calendar)
    app.results_tabs.tab(app.generated, text=f"本批号码 ({len(tickets)})")
    app.results_tabs.select(app.generated)


def generate_post_mode(app, mode):
    try:
        draws = _draws(app)
        config = app.controls.snapshot()
        if mode == CALENDAR_MODE:
            request = app.controls.calendar.snapshot()
        else:
            query = app.controls.conditional.inputs.snapshot()
            front, back = app.controls.conditional.inputs.selected_zones()
            if not (front or back):
                raise ValueError("请勾选前区或后区的条件频次")
    except ValueError as error:
        app.error(error)
        return

    if mode == CALENDAR_MODE:
        def work(cancel, progress):
            samples = select_calendar_samples(draws, request, cancel)
            return generate_calendar_set(config, samples, cancel, progress), samples

        def done(value):
            tickets, samples = value
            _show_tickets(app, tickets, calendar=True)
            app.set_status(f"已生成 15+5、9+3、5+2 · {samples.caption}")
    else:
        def work(cancel, progress):
            report = analyze_conditional_frequency(draws, *query, cancel=cancel)
            weights = conditional_weights(report, front, back)
            return generate(config, cancel=cancel, progress=progress, frequency_weights=weights), report

        def done(value):
            tickets, report = value
            _show_tickets(app, tickets)
            app.statistics.conditional.set_report(report)
            zones = "、".join(label for label, using in (("前区", front), ("后区", back)) if using)
            app.set_status(f"已生成 {len(tickets):,} 组 · 参照 {report.anchor.issue} · "
                           f"下期条件频次（{zones}，回看 {report.history_count:,} 期）")
    app.set_status(f"正在生成 · {mode}…")
    app.jobs.start(work, done, app.error)


def calculate_conditional(app):
    if app.jobs.running:
        app.set_status("请等待当前任务完成，或先取消")
        return
    try:
        draws = _draws(app)
        query = app.conditional_inputs.snapshot()
    except ValueError as error:
        app.error(error)
        return

    def done(report):
        app.statistics.conditional.set_report(report)
        app.set_status(f"已计算下期条件频次 · 参照 {report.anchor.issue} · 回看 {report.history_count:,} 期")

    app.set_status("正在计算下期条件频次…")
    app.jobs.start(lambda cancel, _: analyze_conditional_frequency(draws, *query, cancel=cancel), done, app.error)

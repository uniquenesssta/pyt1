"""通过现有后台任务按期查询奖金，一期只读取一次。"""
from ..core.models import check_cancel
from ..data.prize_notices import fetch_prize_amounts


def lookup_prizes(app, automatic=False):
    panel = app.pick_log.amounts
    pending = dict(panel.pending)
    if not pending:
        return
    if app.jobs.running:
        if not automatic:
            app.set_status("请等待当前任务完成，或先取消")
        return
    panel.attempted.update(pending)

    def work(cancel, progress):
        received, errors = {}, {}
        for key, draw in pending.items():
            check_cancel(cancel)
            progress(f"正在查询第 {draw.issue} 期奖金…")
            try:
                received[key] = fetch_prize_amounts(draw, cancel)
            except (ValueError, OSError) as exc:
                errors[key[0]] = str(exc)
        return received, errors

    def done(result):
        received, errors = result
        panel.notices.update(received)
        app.pick_log.show_detail()
        status = f"已查到 {len(received)} 期奖金"
        if errors:
            issue, error = next(iter(errors.items()))
            status += f"；{len(errors)} 期未查到（第 {issue} 期：{error}）"
        app.set_status(status)

    app.jobs.start(work, done, app.error)

"""协调导入、联网更新与启动恢复，共用后台任务及成功提交入口。"""
from pathlib import Path
from ..core.statistics import analyze
from ..data.importing import load_dataset
from ..data.online_feed import download, parse_feed, validate_update


def apply_history(app, value, message, persist=True):
    dataset, stats = value
    if persist:
        try:
            app.history_store.save(dataset)
        except (OSError, ValueError) as exc:
            app.error(exc)
            return
    app.dataset, app.stats = dataset, stats
    latest = max((d.issue for d in dataset.draws if d.issue), key=int, default='—')
    app.source_text.set(f'{Path(dataset.source).name} · 有效 {len(dataset.draws):,} 行 · 最新期号 {latest} · 无效 {len(dataset.issues):,} 行 · 重复 {dataset.duplicates:,} 行')
    app.history.reset_context()
    app.history.text.set('')
    app.history.set_results([(d, '') for d in dataset.draws], len(dataset.draws))
    app.statistics.set_statistics(stats)
    app.structure_weights.set_history(dataset.draws)
    app.set_status(message)


def import_history(app, path):
    def work(cancel, progress):
        dataset = load_dataset(path, cancel, progress)
        progress(f'正在分析 {len(dataset.draws):,} 条有效记录')
        return dataset, analyze(dataset.draws, cancel)
    app.set_status('正在读取文件…')
    app.jobs.start(work, lambda value: apply_history(app, value, '导入完成并已保存，重启后自动恢复'), app.error)


def update_history(app):
    previous = app.dataset
    def work(cancel, progress):
        incoming = parse_feed(download(cancel, progress), cancel)
        added = validate_update(incoming, previous)
        progress('正在更新统计…')
        return (incoming, analyze(incoming.draws, cancel)), added
    def done(value):
        data, added = value
        apply_history(app, data, f'更新完成：新增 {added:,} 期，共 {len(data[0].draws):,} 期；已保存到本机')
    app.set_status('正在连接开奖数据源…')
    app.jobs.start(work, done, app.error)


def restore_history(app):
    if app.jobs.running or app.dataset is not None:
        return
    def work(cancel, progress):
        dataset = app.history_store.load()
        return (dataset, analyze(dataset.draws, cancel)) if dataset else None
    def done(value):
        if value:
            apply_history(app, value, '已恢复本地历史；点击“更新开奖数据”获取最新记录', persist=False)
    app.jobs.start(work, done, app.error)

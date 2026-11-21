"""对选中的选号记录批量操作，始终用记录索引而非表格行号。"""
from dataclasses import replace
from tkinter import messagebox, simpledialog

from ..core.draw_index import issue_key


def correct_issues(panel):
    indices = panel.selected_indices()
    if not indices:
        return
    effective = set()
    for index in indices:
        record, draw, _, _ = panel.details[index]
        issue = record.issue or (draw.issue if draw else "")
        effective.add(issue_key(issue) if issue else "")
    initial = next(iter(effective)) if len(effective) == 1 else ""
    value = simpledialog.askstring(
        "更正对奖期号",
        f"为选中的 {len(indices)} 条记录输入同一个票面期号。\n留空恢复每条记录自己的自动归期。",
        initialvalue=initial, parent=panel,
    )
    if value is None:
        return
    try:
        text = value.strip()
        issue = issue_key(text) if text else ""
        updated = list(panel.records)
        for index in indices:
            updated[index] = replace(updated[index], issue=issue)
    except ValueError as exc:
        panel.error(exc)
        return
    if updated == panel.records:
        panel.status("选中的记录期号未变")
    elif panel.save(updated):
        panel.reveal_records(indices)
        result = f"按第 {issue} 期核对" if issue else "恢复自动归期"
        panel.status(f"已将 {len(indices)} 条记录{result}")


def delete_selected(panel):
    indices = set(panel.selected_indices())
    if not indices:
        return
    if not messagebox.askyesno("删除选号记录", f"删除选中的 {len(indices)} 条选号记录？\n收藏会保留。",
                               default=messagebox.NO, parent=panel):
        return
    if panel.save([record for i, record in enumerate(panel.records) if i not in indices]):
        panel.status(f"已删除 {len(indices)} 条选号记录")

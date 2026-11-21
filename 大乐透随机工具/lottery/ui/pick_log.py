"""选号记录、期次筛选和对应开奖的号码比对。"""
from dataclasses import replace
from datetime import datetime
import tkinter as tk
from tkinter import simpledialog, ttk

from ..core.draw_calendar import BEIJING
from ..core.draw_index import DrawIndex
from ..core.models import format_numbers
from ..core.pick_records import PickRecord, existing_pick
from ..core.prize_match import compare_pick
from .table import DataTable
from .widgets import wrapped_label


ALL, LATEST, PENDING = "全部记录", "最近已载入期", "待对奖"
LEVEL_NAMES = "一二三四五六七"
EMPTY_NOTE = "在「本批号码」或「我的收藏」中双击一组号码，即可记入这里"


def issue_label(issue):
    return f"第 {issue} 期"


def comparison_label(match):
    if match.prizes is None:
        return "仅对照号码"
    if not match.prizes:
        return "未中"
    level = LEVEL_NAMES[match.prizes[0][0] - 1]
    return f"最高{level}等奖 · 共 {sum(count for _, count in match.prizes):,} 注"


class PickLogPanel(ttk.Frame):
    def __init__(self, parent, store, status, error):
        super().__init__(parent, padding=10)
        self.store, self.status, self.error = store, status, error
        self.history = DrawIndex()
        self.records, self.details = [], {}
        self.load_error = None
        try:
            self.records = store.load()
        except (ValueError, OSError) as exc:
            self.load_error = exc

        self.latest_text = tk.StringVar(self)
        wrapped_label(self, textvariable=self.latest_text, style="Muted.TLabel").pack(fill="x", pady=(0, 6))
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(0, 6))
        self.scope = tk.StringVar(self, value=ALL)
        ttk.Label(toolbar, text="筛选期次").pack(side="left")
        self.scope_box = ttk.Combobox(toolbar, textvariable=self.scope, state="readonly", width=18)
        self.scope_box.pack(side="left", padx=8)
        self.scope_box.bind("<<ComboboxSelected>>", lambda _: self.render())
        self.issue_button = ttk.Button(toolbar, text="更正期号", command=self.edit_issue, state="disabled")
        self.issue_button.pack(side="right")
        wrapped_label(
            toolbar, text="周一、三、六按北京时间 21:00 归期；开奖后可更新数据对奖。",
            style="Muted.TLabel",
        ).pack(side="left", fill="x", expand=True)
        columns = ("保存时间（北京）", "对应期次", "前区号码", "后区号码", "命中数", "对奖结果", "记录索引")
        self.table = DataTable(self, columns, (175, 135, 205, 95, 75, 190, 60),
                               empty_text=EMPTY_NOTE)
        self.table.tree.configure(displaycolumns=columns[:-1])
        self.table.pack(fill="both", expand=True)
        self.detail = tk.StringVar(self)
        wrapped_label(self, textvariable=self.detail, style="Muted.TLabel").pack(
            side="bottom", before=self.table, fill="x", pady=(6, 0))
        self.table.tree.bind("<<TreeviewSelect>>", lambda _: self.show_detail(), add="+")
        self.set_history(())

    def set_history(self, draws):
        self.history = DrawIndex(draws)
        latest = self.history.latest
        if self.history.latest_conflict:
            note = f"最近已载入期 {self.history.latest_conflict} 存在冲突，请核对开奖数据"
        elif latest:
            note = f"最近已载入：{issue_label(latest.issue)} {latest.draw_date} · {latest.ticket.text()}"
        else:
            note = "尚无带期号的开奖数据；可更新或导入历史后对奖。"
        self.latest_text.set(note)
        self.render()

    def save(self, records):
        try:
            if self.load_error is not None:
                raise self.load_error
            self.store.save(records)
        except (ValueError, OSError) as exc:
            self.error(exc)
            return False
        self.records = records
        self.render()
        return True

    def record(self, ticket, *, saved_at=None, reveal=False):
        pick = PickRecord.from_selection(ticket, saved_at if saved_at is not None else datetime.now(BEIJING))
        previous = existing_pick(self.records, pick, self.history)
        if previous:
            index, message = self.records.index(previous), "该号码已记录"
        elif self.save(self.records + [pick]):
            index, message = len(self.records) - 1, "已保存选号记录"
        else:
            return ""
        if reveal:
            self.reveal_record(index)
        return f"{message} · 预计开奖日 {pick.target_date}"

    def reveal_record(self, index):
        table = self.table

        def position():
            return next((i for i, row in enumerate(table.rows) if row[-1] == index), None)

        row = position()
        if row is None:
            self.scope.set(ALL)
            self.render()
            row = position()
        if row is not None:
            table.go_to_page(row // table.PAGE_SIZE)
            item = str(row)
            table.tree.selection_set(item)
            table.tree.focus(item)
            table.tree.see(item)
            self.show_detail()

    def render(self):
        entries = []
        self.details = {}
        latest = self.history.latest
        for index in range(len(self.records) - 1, -1, -1):
            record = self.records[index]
            draw, waiting = self.history.resolve(record)
            match = compare_pick(record.ticket, draw) if draw else None
            issue = draw.issue if draw else record.issue
            period = issue_label(issue) if issue else f"预计 {record.target_date}"
            row = (record.saved_at.strftime("%Y-%m-%d %H:%M:%S"), period,
                   format_numbers(record.ticket.front), format_numbers(record.ticket.back),
                   f"{len(match.front)}+{len(match.back)}" if match else "—",
                   comparison_label(match) if match else waiting, index)
            entries.append((period, draw, row))
            self.details[index] = (record, draw, match, waiting)

        scopes = (ALL, LATEST, PENDING) + tuple(dict.fromkeys(period for period, _, _ in entries))
        self.scope_box.configure(values=scopes)
        if self.scope.get() not in scopes:
            self.scope.set(ALL)
        scope = self.scope.get()
        self.table.set_rows(row for period, draw, row in entries
                            if scope in (ALL, period)
                            or (scope == LATEST and latest is not None and draw == latest)
                            or (scope == PENDING and draw is None))
        if self.load_error:
            self.table.empty.configure(text=str(self.load_error).splitlines()[0])
        elif self.records:
            self.table.empty.configure(text="当前期次没有选号记录")
        else:
            self.table.empty.configure(text=EMPTY_NOTE)
        self.show_detail()

    def selected_index(self):
        rows = self.table.selected()
        return rows[0][-1] if len(rows) == 1 else None

    def show_detail(self):
        index = self.selected_index()
        self.issue_button.configure(state="disabled" if index is None or self.load_error else "normal")
        if index is None:
            self.detail.set("选中一条查看开奖号码、命中的号码或更正期号。")
            return
        record, draw, match, waiting = self.details[index]
        saved = record.saved_at.strftime("%Y-%m-%d %H:%M:%S")
        if draw is None:
            target = issue_label(record.issue) if record.issue else f"预计开奖日 {record.target_date}"
            self.detail.set(f"{saved} 保存 · {target} · {waiting}；若休市或数据没有日期，可按票面更正期号。")
            return
        prizes = ""
        if match.prizes:
            prizes = " · " + "、".join(f"{LEVEL_NAMES[level - 1]}等奖 {count:,} 注" for level, count in match.prizes)
        self.detail.set(
            f"{saved} 保存 · {issue_label(draw.issue)} {draw.draw_date} · 开奖 {draw.ticket.text()} · "
            f"命中前区 {format_numbers(match.front) or '无'} / 后区 {format_numbers(match.back) or '无'}{prizes}"
        )

    def edit_issue(self):
        index = self.selected_index()
        if index is None:
            return
        record, current, _, _ = self.details[index]
        value = simpledialog.askstring(
            "更正对奖期号", "输入票面期号；留空恢复按预计开奖日匹配。",
            initialvalue=record.issue or (current.issue if current else ""), parent=self,
        )
        if value is None:
            return
        try:
            changed = replace(record, issue=value.strip())
        except ValueError as exc:
            self.error(exc)
            return
        updated = list(self.records)
        updated[index] = changed
        if self.save(updated):
            self.reveal_record(index)
            self.status(f"已改为按{issue_label(changed.issue)}核对" if changed.issue else "已恢复按预计开奖日核对")

"""选号记录、期次筛选和对应开奖的号码比对。"""
from datetime import datetime
import tkinter as tk
from tkinter import ttk

from ..core.draw_calendar import BEIJING
from ..core.draw_index import DrawIndex
from ..core.models import format_numbers
from ..core.pick_records import prepare_pick_batch
from ..core.prize_match import compare_pick
from .pick_log_actions import correct_issues, delete_selected
from .prize_amount_panel import PrizeAmountPanel
from .table import DataTable
from .widgets import wrapped_label


ALL, LATEST, PENDING = "全部记录", "最近已载入期", "待对奖"
LEVEL_NAMES = "一二三四五六七"
EMPTY_NOTE = "在「我的收藏」选中号码后点击「记录选号」；也可双击一组直接记录"


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
    def __init__(self, parent, store, status, error, lookup_prizes):
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
        self.delete_button = ttk.Button(toolbar, text="删除选中", command=lambda: delete_selected(self), state="disabled")
        self.delete_button.pack(side="right")
        self.issue_button = ttk.Button(toolbar, text="更正期号", command=lambda: correct_issues(self), state="disabled")
        self.issue_button.pack(side="right", padx=(0, 8))
        wrapped_label(
            toolbar, text="周一、三、六按北京时间 21:00 归期；开奖后可更新数据对奖。",
            style="Muted.TLabel",
        ).pack(side="left", fill="x", expand=True)
        columns = ("保存时间（北京）", "对应期次", "前区号码", "后区号码", "命中数", "对奖结果", "记录索引")
        self.table = DataTable(self, columns, (175, 135, 205, 95, 75, 190, 60),
                               empty_text=EMPTY_NOTE)
        self.table.tree.configure(displaycolumns=columns[:-1])
        self.table.pack(fill="both", expand=True)
        footer = ttk.Frame(self)
        footer.pack(side="bottom", before=self.table, fill="x", pady=(6, 0))
        self.detail = tk.StringVar(self)
        wrapped_label(footer, textvariable=self.detail, style="Muted.TLabel").pack(fill="x")
        self.amounts = PrizeAmountPanel(footer, lookup_prizes)
        self.amounts.pack(fill="x", pady=(4, 0))
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

    def record_many(self, tickets, *, saved_at=None, reveal=False):
        now = saved_at if saved_at is not None else datetime.now(BEIJING)
        added, indices, target = prepare_pick_batch(self.records, tickets, now, self.history)
        if not indices or (added and not self.save(self.records + added)):
            return ""
        if reveal:
            self.reveal_records(indices)
        existing = len(indices) - len(added)
        if not added:
            message = f"所选 {existing} 条已记录"
        else:
            message = f"已保存 {len(added)} 条选号记录"
            if existing:
                message += f" · 本期已有 {existing} 条"
        return f"{message} · 预计开奖日 {target}"

    def reveal_records(self, indices):
        table = self.table
        wanted = set(indices)

        def positions():
            return [i for i, row in enumerate(table.rows) if row[-1] in wanted]

        rows = positions()
        if len(rows) < len(wanted) and self.scope.get() != ALL:
            self.scope.set(ALL)
            self.render()
            rows = positions()
        if rows:
            page = rows[0] // table.PAGE_SIZE
            table.go_to_page(page)
            table.tree.selection_set(*(str(row) for row in rows if row // table.PAGE_SIZE == page))
            table.tree.focus(str(rows[0]))
            table.tree.see(str(rows[0]))
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
        indices = self.selected_indices()
        return indices[0] if len(indices) == 1 else None

    def selected_indices(self):
        return tuple(row[-1] for row in self.table.selected())

    def show_detail(self):
        indices = self.selected_indices()
        state = "normal" if indices and not self.load_error else "disabled"
        self.issue_button.configure(state=state)
        self.delete_button.configure(state=state)
        self.amounts.show([self.details[index] for index in indices])
        if not indices:
            self.detail.set("选中记录查看命中；Ctrl / Shift 可多选、更正期号或删除。")
            return
        if len(indices) > 1:
            self.detail.set(f"已选 {len(indices)} 条记录，可一起更正期号或删除。")
            return
        index = indices[0]
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

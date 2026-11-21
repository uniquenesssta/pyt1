"""显示所选记录的基本投注金额，缺数据时查询对应开奖的奖金。"""
from tkinter import ttk

from ..core.draw_index import issue_key
from ..core.prize_amounts import basic_amount
from .widgets import wrapped_label


def draw_key(draw):
    return issue_key(draw.issue), draw.draw_date, draw.ticket


class PrizeAmountPanel(ttk.Frame):
    def __init__(self, parent, lookup):
        super().__init__(parent)
        self.lookup = lookup
        self.busy = False
        self.timer = None
        self.notices, self.pending = {}, {}
        self.attempted = set()
        self.button = ttk.Button(self, text="查询奖金", state="disabled", command=lambda: lookup(False))
        self.button.pack(side="right")
        self.label = wrapped_label(self, style="Muted.TLabel")
        self.label.pack(side="left", fill="x", expand=True)
        self.bind("<Map>", lambda _: self.sync())
        self.show(())

    def show(self, entries):
        self.pending = {}
        if not entries:
            self.label.configure(text="中奖金额（基本投注 1 倍 · 税前）：选中记录查看")
            self.sync()
            return
        subtotal = known = waiting = legacy = partial = 0
        unavailable = set()
        for _, draw, match, _ in entries:
            if match is None:
                waiting += 1
            elif match.prizes is None:
                legacy += 1
            elif not match.prizes:
                known += 1
            else:
                key = draw_key(draw)
                amounts = self.notices.get(key)
                if amounts is None:
                    self.pending[key] = draw
                    unavailable.add(key)
                else:
                    amount, missing = basic_amount(match.prizes, amounts)
                    subtotal += amount
                    known += not missing
                    partial += bool(missing)
                    if missing:
                        self.pending[key] = draw
        qualifier = "合计" if len(entries) > 1 else ""
        result = f"中奖金额{qualifier}（基本投注 1 倍 · 税前）："
        if partial or waiting or legacy or self.pending:
            result += f"已知 {subtotal:,} 元" if subtotal or known else "—"
            if waiting:
                result += f" · {waiting} 条尚无对应开奖"
            if legacy:
                result += f" · {legacy} 条为旧奖级，仅对照号码"
            if unavailable:
                result += f" · {len(unavailable)} 期奖金待查"
            if partial:
                result += f" · {partial} 条的单注奖金不完整"
        else:
            result += f"{subtotal:,} 元"
        self.label.configure(text=result)
        self.sync()

    def set_busy(self, busy):
        self.busy = busy
        self.sync()

    def sync(self):
        self.button.configure(state="normal" if self.pending and not self.busy else "disabled")
        if self.timer is None and not self.busy and self.winfo_ismapped() and len(self.pending) == 1:
            if next(iter(self.pending)) not in self.attempted:
                self.timer = self.after(250, self.auto_lookup)

    def auto_lookup(self):
        self.timer = None
        if not self.busy and self.winfo_ismapped() and len(self.pending) == 1:
            if next(iter(self.pending)) not in self.attempted:
                self.lookup(True)

    def close(self):
        if self.timer is not None:
            self.after_cancel(self.timer)
            self.timer = None

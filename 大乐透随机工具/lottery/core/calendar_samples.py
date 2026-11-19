"""同星期和历年同序号的样本选择，严格排除目标期及以后。"""
from dataclasses import dataclass
from datetime import date, timedelta

from .draw_calendar import DRAW_WEEKDAYS
from .draw_index import issue_key
from .history_window import ordered_history
from .models import check_cancel


CALENDAR_MODE = "同星期 / 历年同期"
WEEKDAY_LABELS = {0: "周一", 2: "周三", 5: "周六"}


@dataclass(frozen=True)
class CalendarRequest:
    target_issue: str = ""
    weekday: int | None = None
    recent_days: int = 9
    past_years: int = 9

    def validate(self):
        if self.weekday is not None and self.weekday not in DRAW_WEEKDAYS:
            raise ValueError("开奖星期须为周一、周三或周六")
        if (type(self.recent_days) is not int or type(self.past_years) is not int
                or not 0 <= self.recent_days <= 500 or not 0 <= self.past_years <= 99):
            raise ValueError("同星期次数须为 0–500、历年同期年数须为 0–99")
        if not (self.recent_days or self.past_years):
            raise ValueError("至少选择一种历史样本；填 0 跳过对应窗口")


@dataclass(frozen=True)
class CalendarSamples:
    target_issue: str
    weekday: int | None
    estimated: bool
    same_weekday: tuple
    same_ordinal: tuple
    draws: tuple

    @property
    def caption(self):
        when = WEEKDAY_LABELS.get(self.weekday, "")
        status = "（预计）" if self.estimated else ""
        return (f"目标 {self.target_issue} {when}{status} · 同星期 {len(self.same_weekday)} 期 / "
                f"历年同期 {len(self.same_ordinal)} 期 · 去重后 {len(self.draws)} 期")


def _lottery_issue(issue):
    try:
        key = issue_key(issue)
    except ValueError:
        key = ""
    if len(key) != 5 or int(key[2:]) == 0:
        raise ValueError("目标期号请用 5 位（如 26132）或 7 位（如 2026132）格式")
    return key


def _next_target(last):
    issue = _lottery_issue(last.issue)
    if not last.draw_date:
        return None, None
    day = date.fromisoformat(last.draw_date) + timedelta(days=1)
    while day.weekday() not in DRAW_WEEKDAYS:
        day += timedelta(days=1)
    ordinal = int(issue[2:]) + 1 if day.year % 100 == int(issue[:2]) else 1
    return f"{day.year%100:02d}{ordinal:03d}", day


def select_calendar_samples(draws, request, cancel=None):
    request.validate()
    check_cancel(cancel)
    ordered, _ = ordered_history(draws)
    if not ordered[-1].issue:
        raise ValueError("同星期／历年同期需要带期号的开奖记录")

    issue = _lottery_issue(request.target_issue) if request.target_issue else ""
    reference = next((d for d in ordered if issue_key(d.issue) == issue), None)
    estimated = reference is None
    inferred_day = None
    if reference is not None:
        if reference.draw_date:
            inferred_day = date.fromisoformat(reference.draw_date)
    else:
        next_issue, next_day = _next_target(ordered[-1])
        if not issue:
            if not next_issue:
                raise ValueError("最新期开奖缺日期；请更新开奖数据，或手填目标期号和星期")
            issue = next_issue
        if issue == next_issue:
            inferred_day = next_day

    inferred_weekday = inferred_day.weekday() if inferred_day else None
    weekday = inferred_weekday if request.weekday is None else request.weekday
    if reference and inferred_weekday is not None and weekday != inferred_weekday:
        raise ValueError(f"第 {issue} 期实际开奖为{WEEKDAY_LABELS.get(inferred_weekday, '其他星期')}，请将星期选为自动")
    if request.recent_days and weekday is None:
        raise ValueError("找不到目标开奖星期；请选周一、周三或周六，或更新开奖日期")

    weekly, annual = [], []
    for index, draw in enumerate(ordered):
        if index % 128 == 0:
            check_cancel(cancel)
        key = issue_key(draw.issue)
        if int(key) >= int(issue):
            break
        if inferred_day and draw.draw_date and draw.draw_date >= inferred_day.isoformat():
            continue
        if request.recent_days and draw.draw_date and date.fromisoformat(draw.draw_date).weekday() == weekday:
            weekly.append(draw)
        if request.past_years and len(key) == 5 and key[:2] < issue[:2] and key[2:] == issue[2:]:
            annual.append(draw)

    weekly = tuple(weekly[-request.recent_days:]) if request.recent_days else ()
    annual = tuple(annual[-request.past_years:]) if request.past_years else ()
    if request.recent_days and not weekly:
        raise ValueError("没有目标期之前的同星期样本；请核对日期或将同星期次数设为 0")
    if request.past_years and not annual:
        raise ValueError("没有目标期之前的历年同期样本；请补充历史或将同期年数设为 0")
    by_issue = {int(issue_key(draw.issue)): draw for draw in weekly + annual}
    check_cancel(cancel)
    return CalendarSamples(issue, weekday, estimated, weekly, annual, tuple(by_issue[k] for k in sorted(by_issue)))

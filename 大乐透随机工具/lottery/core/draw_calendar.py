"""按北京时间的停售时间为选号记录标出预计开奖日。"""
from datetime import time, timedelta, timezone


BEIJING = timezone(timedelta(hours=8), "北京时间")
DRAW_WEEKDAYS = (0, 2, 5)
SALE_CUTOFF = time(21, 0)


def beijing_time(value):
    if value.utcoffset() is None:
        raise ValueError("保存时间缺少时区")
    return value.astimezone(BEIJING)


def expected_draw_date(saved_at):
    local = beijing_time(saved_at)
    day = local.date()
    if local.time() >= SALE_CUTOFF:
        day += timedelta(days=1)
    while day.weekday() not in DRAW_WEEKDAYS:
        day += timedelta(days=1)
    return day

"""读取公开开奖详情中的基本奖级金额，先核对期号、号码与日期。"""
from datetime import date
import json
import re
from urllib.request import Request, urlopen

from ..core.draw_index import issue_key
from ..core.models import Ticket, check_cancel


NOTICE_URL = "https://www.ydniu.com/open/dlt/20{issue}.html"
NOTICE_MAX_BYTES = 1_000_000
PRIZE_LABELS = tuple(f"{name}等奖" for name in "一二三四五六七")


def _field(page, pattern, label):
    found = re.findall(pattern, page, re.S)
    if len(found) != 1:
        raise ValueError(f"开奖详情缺失或无法确认{label}")
    return found[0]


def parse_prize_page(page, draw):
    head = _field(page, r'<div\s+class=["\']gg_ssq gg_dlt["\']>\s*<dl\b[^>]*>(.*?)</dl>', "本期开奖区")
    issue = _field(head, r'class=["\']ggissue_name["\']>大乐透第\s*<strong>([0-9]+)</strong>\s*期', "期号")
    date_text = _field(head, r'id=["\']openDate["\']>开奖日期[：:]\s*(\d{4}年\d{1,2}月\d{1,2}日)', "开奖日期")
    day = date(*map(int, re.findall(r"\d+", date_text))).isoformat()
    balls = _field(head, r'<p\s+class=["\']number dlt-number["\']>(.*?)</p>', "开奖号码")
    numbers = tuple(map(int, re.findall(r"<span(?:\s[^>]*)?>\s*([0-9]{1,2})\s*</span>", balls)))
    if (len(numbers) != 7 or issue_key(draw.issue) != issue_key(issue)
            or (draw.draw_date and draw.draw_date != day)
            or draw.ticket != Ticket(numbers[:5], numbers[5:])):
        raise ValueError(f"第 {draw.issue} 期开奖详情与历史记录不一致")

    payload = _field(page, r"\bissue_current_WinType\s*=\s*JSON\.parse\('([^']*)'\)", "奖金表")
    groups = json.loads(payload)
    if (not isinstance(groups, list) or len(groups) != 1 or not isinstance(groups[0], list)
            or any(not isinstance(row, dict) for row in groups[0])):
        raise ValueError("奖金表格式异常")
    amounts = {}
    for row in groups[0]:
        name = row.get("Name")
        if name not in PRIZE_LABELS:
            continue
        amount = row.get("WinMoney")
        if (name in amounts or (amount is not None and (type(amount) is not int or amount < 0))):
            raise ValueError(f"{name}的单注奖金无法确认")
        amounts[name] = amount or None
    if not any(amounts.values()):
        raise ValueError("未取得可用的基本投注奖金")
    return tuple(amounts.get(name) for name in PRIZE_LABELS)


def fetch_prize_amounts(draw, cancel=None):
    issue = issue_key(draw.issue)
    if len(issue) != 5 or int(issue) < 26014:
        raise ValueError("此期未使用当前七奖级规则")
    check_cancel(cancel)
    request = Request(NOTICE_URL.format(issue=issue), headers={"User-Agent": "LotteryHistoryTool/1.0",
                                                               "Accept": "text/html"})
    with urlopen(request, timeout=8) as response:
        raw = response.read(NOTICE_MAX_BYTES + 1)
    check_cancel(cancel)
    if not raw or len(raw) > NOTICE_MAX_BYTES:
        raise ValueError("开奖详情文件大小异常")
    return parse_prize_page(raw.decode("utf-8-sig"), draw)

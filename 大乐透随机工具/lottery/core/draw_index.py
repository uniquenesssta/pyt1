"""用真实开奖日期或期号定位结果，遇到冲突时不代填其他期。"""
from collections import defaultdict
import re


def issue_key(issue):
    if not re.fullmatch(r"[0-9]{3,12}", issue):
        raise ValueError("期号请输入 3–12 位数字")
    # 同一期可由数据源写为 26132 或 2026132。
    return issue[2:] if len(issue) == 7 and issue.startswith("20") else issue


class DrawIndex:
    def __init__(self, draws=()):
        groups = defaultdict(list)
        self.by_date = defaultdict(set)
        for draw in draws:
            if draw.issue:
                key = issue_key(draw.issue)
                groups[key].append(draw)
                if draw.draw_date:
                    self.by_date[draw.draw_date].add(key)
        self.by_issue = {}
        self.conflicts = set()
        for key, group in groups.items():
            dates = {d.draw_date for d in group if d.draw_date}
            if len(dates) > 1 or len({d.ticket for d in group}) > 1:
                self.conflicts.add(key)
            else:
                self.by_issue[key] = next((d for d in group if d.draw_date), group[0])
        last = max(groups, key=int, default="")
        self.latest = self.by_issue.get(last)
        self.latest_conflict = last if last in self.conflicts else ""
        self.last_date = max(self.by_date, default="")

    def resolve(self, record):
        if record.issue:
            key = issue_key(record.issue)
        else:
            day = record.target_date.isoformat()
            matches = self.by_date.get(day, ())
            if not matches:
                if day <= self.last_date:
                    return None, "未找到当日开奖"
                return None, "待开奖数据"
            if len(matches) != 1:
                return None, "开奖日期有冲突"
            key = next(iter(matches))
        if key in self.conflicts:
            return None, "同期开奖数据冲突"
        draw = self.by_issue.get(key)
        return draw, "" if draw else "待开奖数据"

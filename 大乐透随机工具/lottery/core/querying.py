"""按整数和区域匹配，避免字符串子串误命中。"""
from dataclasses import dataclass
from .models import parse_numbers, check_cancel


@dataclass(frozen=True)
class Query:
    text: str = ""
    kind: str = "号码"
    area: str = "全部"
    mode: str = "包含全部"


def search(draws, query, cancel=None):
    text = query.text.strip()
    if query.kind not in ("号码", "期号") or query.area not in ("全部", "前区", "后区"):
        raise ValueError("未知的查询类型或区域")
    valid_modes = ("包含全部", "包含任意", "连续位置") if query.kind == "号码" else ("完全一致", "前缀", "后三位")
    if query.mode not in valid_modes:
        raise ValueError("未知的匹配方式")
    if query.kind == "期号" and text and not text.isascii():
        raise ValueError("期号请填写数字")
    if query.kind == "期号" and text and not text.isdigit():
        raise ValueError("期号请填写数字")
    if query.kind == "期号" and query.mode == "后三位" and text and len(text) != 3:
        raise ValueError("后三位查询请填写恰好 3 位数字")
    targets = parse_numbers(text, 12 if query.area == "后区" else 35, preserve_order=True) if query.kind == "号码" else ()
    results = []
    for i, draw in enumerate(draws):
        if i % 256 == 0:
            check_cancel(cancel)
        if not text:
            results.append((draw, ""))
            continue
        if query.kind == "期号":
            match = bool(draw.issue) and {"完全一致": draw.issue == text,
                "前缀": draw.issue.startswith(text), "后三位": draw.issue[-3:] == text}[query.mode]
            if match:
                results.append((draw, "期号" + query.mode))
            continue
        areas = []
        if query.area in ("全部", "前区"):
            areas.append(("前区", draw.ticket.front))
        if query.area in ("全部", "后区"):
            areas.append(("后区", draw.ticket.back))
        pool = set(n for _, nums in areas for n in nums)
        positions = [f"{label}第{i+1}位" for label, nums in areas for i, n in enumerate(nums) if n in targets]
        if query.mode == "连续位置":
            positions = [f"{label}第{i+1}位开始" for label, nums in areas
                         for i in range(len(nums)-len(targets)+1) if nums[i:i+len(targets)] == targets]
            match = bool(positions)
        elif query.mode == "包含全部":
            match = set(targets) <= pool
        else:
            match = bool(set(targets) & pool)
        if match:
            results.append((draw, "、".join(positions)))
    check_cancel(cancel)
    return results

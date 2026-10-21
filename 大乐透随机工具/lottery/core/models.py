"""共享数据模型与输入约束。"""
from dataclasses import dataclass
from math import comb
import re


def validate_numbers(numbers, maximum, minimum_count, maximum_count, label):
    values = tuple(numbers)
    if not minimum_count <= len(values) <= maximum_count:
        raise ValueError(f"{label}数量须为 {minimum_count}–{maximum_count}")
    if any(type(n) is not int or not 1 <= n <= maximum for n in values):
        raise ValueError(f"{label}号码须为 1–{maximum} 的整数")
    if len(set(values)) != len(values):
        raise ValueError(f"{label}号码不能重复")
    return tuple(sorted(values))


def parse_numbers(text, maximum=35, label="号码", preserve_order=False):
    if not text.strip():
        return ()
    tokens = re.split(r"[\s,，、;；]+", text.strip())
    if any(not re.fullmatch(r"[0-9]{1,2}", t) for t in tokens):
        raise ValueError(f"{label}请用空格或逗号分隔整数")
    values = tuple(map(int, tokens))
    validated = validate_numbers(values, maximum, 0, maximum, label)
    return values if preserve_order else validated


@dataclass(frozen=True)
class Ticket:
    front: tuple[int, ...]
    back: tuple[int, ...]

    def __post_init__(self):
        object.__setattr__(self, "front", validate_numbers(self.front, 35, 5, 35, "前区"))
        object.__setattr__(self, "back", validate_numbers(self.back, 12, 2, 12, "后区"))

    @property
    def bets(self):
        # 固定号码仅约束随机选号；输出为普通单式/复式，不冒充胆拖票。
        return comb(len(self.front), 5) * comb(len(self.back), 2)

    def text(self):
        return f"{format_numbers(self.front)} | {format_numbers(self.back)}"


def format_numbers(numbers):
    return " ".join(f"{n:02d}" for n in numbers)


@dataclass(frozen=True)
class Draw:
    ticket: Ticket
    issue: str = ""
    line: int = 0
    sheet: str = ""

    def __post_init__(self):
        if len(self.ticket.front) != 5 or len(self.ticket.back) != 2:
            raise ValueError("历史记录必须为 5 个前区号码和 2 个后区号码")


class Cancelled(Exception):
    """用户取消；调用方保留上次完整结果。"""


def check_cancel(cancel):
    if cancel is not None and cancel.is_set():
        raise Cancelled("操作已取消，上次结果已保留")

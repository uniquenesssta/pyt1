"""铜钱点数对应的四种爻，以及动爻变化规则。"""
from dataclasses import dataclass


YAO_NAMES = ("初爻", "二爻", "三爻", "四爻", "五爻", "上爻")
YANG_SYMBOL = "—————"
YIN_SYMBOL = "—   —"


@dataclass(frozen=True)
class Yao:
    value: int
    name: str
    symbol: str
    is_yang: bool
    is_changing: bool

    @property
    def changed_is_yang(self):
        return not self.is_yang if self.is_changing else self.is_yang

    @property
    def changed_symbol(self):
        return YANG_SYMBOL if self.changed_is_yang else YIN_SYMBOL


YAO_TYPES = {
    6: Yao(6, "老阴", "— X —", False, True),
    7: Yao(7, "少阳", YANG_SYMBOL, True, False),
    8: Yao(8, "少阴", YIN_SYMBOL, False, False),
    9: Yao(9, "老阳", "— O —", True, True),
}


@dataclass(frozen=True)
class Hexagram:
    # 按初爻至上爻保存；界面自上向下反向排列。
    lines: tuple[Yao, ...]

    def __post_init__(self):
        if len(self.lines) != 6:
            raise ValueError("一卦必须包含六个爻。")

    @property
    def has_changes(self):
        return any(line.is_changing for line in self.lines)

    @property
    def changed_symbols(self):
        return tuple(line.changed_symbol for line in self.lines)

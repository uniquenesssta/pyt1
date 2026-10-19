"""六十四卦资料与按初爻至上爻排列的卦画检索。"""
from dataclasses import dataclass


@dataclass(frozen=True)
class LineText:
    label: str
    text: str


@dataclass(frozen=True)
class ReadingNotes:
    keywords: tuple[str, ...]
    summary: str
    opportunity: str
    caution: str


@dataclass(frozen=True)
class ClassicHexagram:
    number: int
    name: str
    full_name: str
    pattern: str
    lower: str
    upper: str
    judgement: str
    lines: tuple[LineText, ...]
    special: tuple[LineText, ...]
    image: str
    source_title: str
    source_url: str
    source_revision_url: str
    notes: ReadingNotes

    @property
    def display_name(self):
        return f"{self.full_name} · 第{self.number}卦"


class HexagramCatalog:
    def __init__(self, entries):
        self.entries = tuple(sorted(entries, key=lambda entry: entry.number))
        self._by_pattern = {entry.pattern: entry for entry in self.entries}
        if len(self.entries) != 64 or len(self._by_pattern) != 64:
            raise ValueError("卦象资料必须包含互不重复的六十四卦。")
        if {entry.number for entry in self.entries} != set(range(1, 65)):
            raise ValueError("卦序资料不完整。")

    def identify(self, hexagram, changed=False):
        pattern = "".join(
            "1" if (line.changed_is_yang if changed else line.is_yang) else "0"
            for line in hexagram.lines
        )
        return self._by_pattern[pattern]

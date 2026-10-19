"""生成有明确依据的多角度参考，不为 4096 种组合预写结论。"""
from dataclasses import dataclass

from ..domain.hexagrams import ClassicHexagram, LineText
from .context import Topic, match_topics


POSITION_QUESTIONS = (
    "起步所需的基础是否已经具备？有什么适合先小范围尝试？",
    "日常推进与配合是否顺畅？哪些行动能够形成稳定支持？",
    "从准备走向进一步行动时，是否出现过度用力或衔接不足？",
    "进入新位置或面对外部条件时，需要重新确认哪些支持和边界？",
    "关键责任与决定由谁承担？已有条件怎样落实为合适的安排？",
    "当前阶段是否接近边界？哪些事情需要收束、复查或转向？",
)


@dataclass(frozen=True)
class MovingLine:
    position: int
    label: str
    text: str
    change: str
    question: str


@dataclass(frozen=True)
class ReadingReport:
    question: str
    background: str
    original: ClassicHexagram
    changed: ClassicHexagram
    moving: tuple[MovingLine, ...]
    topics: tuple[Topic, ...]
    special: tuple[LineText, ...]


def analyze(hexagram, catalog, question="", background=""):
    original = catalog.identify(hexagram)
    changed = catalog.identify(hexagram, changed=True)
    moving = tuple(
        MovingLine(
            index + 1, original.lines[index].label, original.lines[index].text,
            "阳 → 阴" if line.is_yang else "阴 → 阳", POSITION_QUESTIONS[index],
        )
        for index, line in enumerate(hexagram.lines) if line.is_changing
    )
    special = original.special if len(moving) == 6 else ()
    return ReadingReport(question.strip(), background.strip(), original, changed,
                         moving, match_topics(question, background), special)

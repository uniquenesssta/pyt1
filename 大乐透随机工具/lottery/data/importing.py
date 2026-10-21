"""严格解析完整行；拒绝将期号、坏后区或多余数字混入统计。"""
from dataclasses import dataclass, field
from pathlib import Path
import re
from ..core.models import Draw, Ticket, check_cancel


@dataclass(frozen=True)
class ImportIssue:
    line: int
    reason: str
    text: str


@dataclass
class Dataset:
    draws: list = field(default_factory=list)
    issues: list = field(default_factory=list)
    ignored: int = 0
    duplicates: int = 0
    encoding: str = ""
    source: str = ""


def parse_line(line, line_number=0):
    cleaned = re.sub(r"前区\s*[:：]?|后区\s*[:：]?", " ", line.strip())
    tokens = re.split(r"[\s,，、;；|+]+", cleaned.strip())
    issue = ""
    if len(tokens) == 8:
        issue = tokens.pop(0)
        if not re.fullmatch(r"[0-9]{3,12}", issue):
            raise ValueError("期号须为 3–12 位数字；日期列请先移除")
    if len(tokens) != 7:
        raise ValueError("需要 7 个号码，或期号加 7 个号码")
    if any(not re.fullmatch(r"[0-9]{1,2}", t) for t in tokens):
        raise ValueError("号码必须为整数，不能包含日期、负数或小数")
    numbers = list(map(int, tokens))
    return Draw(Ticket(tuple(numbers[:5]), tuple(numbers[5:])), issue, line_number)


def parse_text(text, cancel=None, progress=None):
    result = Dataset()
    seen = set()
    for line_number, raw in enumerate(text.splitlines(), 1):
        if line_number % 256 == 0:
            check_cancel(cancel)
            if progress:
                progress(f"已解析 {line_number:,} 行")
        line = raw.strip()
        if not line or line.startswith("#"):
            result.ignored += 1
            continue
        try:
            draw = parse_line(line, line_number)
            # 保留原始每一行，统计重复数；不同期号的相同号码不是重复记录。
            key = (draw.issue, draw.ticket)
            if key in seen:
                result.duplicates += 1
            seen.add(key)
            result.draws.append(draw)
        except ValueError as error:
            result.issues.append(ImportIssue(line_number, str(error), raw))
    check_cancel(cancel)
    return result


def load_dataset(path, cancel=None, progress=None):
    if Path(path).suffix.lower() in {".xls", ".xlsx", ".xlxs"}:
        from .excel import load_excel
        result = load_excel(path, cancel, progress)
        if not result.draws:
            detail = result.issues[0].reason if result.issues else "工作簿为空"
            raise ValueError(f"没有有效的 5+2 记录：{detail}")
        return result
    raw = Path(path).read_bytes()
    check_cancel(cancel)
    encodings = ["utf-16"] if raw.startswith((b"\xff\xfe", b"\xfe\xff")) else ["utf-8-sig", "gb18030"]
    for encoding in encodings:
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError("无法解码文件，请另存为 UTF-8 文本")
    result = parse_text(text, cancel, progress)
    result.encoding, result.source = encoding, str(path)
    if not result.draws:
        detail = result.issues[0].reason if result.issues else "文件为空或只有注释"
        raise ValueError(f"没有有效的 5+2 记录：{detail}")
    return result

"""加载、校验并缓存每卦独立保存的资料。"""
import json
from functools import lru_cache
from pathlib import Path

from ..domain.hexagrams import ClassicHexagram, HexagramCatalog, LineText, ReadingNotes


RESOURCE_DIRECTORY = Path(__file__).resolve().parents[2] / "resources" / "hexagrams"


def load_catalog(directory=RESOURCE_DIRECTORY):
    entries = []
    for path in sorted(Path(directory).glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        pattern = data["pattern"]
        lines = tuple(LineText(**line) for line in data["lines"])
        if len(pattern) != 6 or set(pattern) - {"0", "1"} or len(lines) != 6:
            raise ValueError(f"卦画或爻辞资料不完整：{path.name}")
        for bit, line in zip(pattern, lines):
            if ("九" if bit == "1" else "六") not in line.label or not line.text.strip():
                raise ValueError(f"爻辞与卦画不对应：{path.name}")
        if not data["judgement"].strip() or not data["image"].strip():
            raise ValueError(f"卦辞或大象资料缺失：{path.name}")
        source, notes = data["source"], data["editorial"]
        entries.append(ClassicHexagram(
            number=data["number"], name=data["name"], full_name=data["full_name"],
            pattern=pattern, lower=data["lower"], upper=data["upper"],
            judgement=data["judgement"], lines=lines,
            special=tuple(LineText(**line) for line in data["special"]), image=data["image"],
            source_title=source["title"], source_url=source["url"],
            source_revision_url=source["revision_url"],
            notes=ReadingNotes(tuple(notes["keywords"]), notes["summary"],
                               notes["opportunity"], notes["caution"]),
        ))
    return HexagramCatalog(entries)


@lru_cache(maxsize=1)
def get_catalog():
    return load_catalog()

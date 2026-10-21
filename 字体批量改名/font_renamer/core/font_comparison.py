"""字体比较信息：完整名称、字重样式、版本、字符覆盖。"""
from dataclasses import dataclass
from pathlib import Path
from .duplicates import fingerprint
from .reader import TTFont, decode_name_record, platform_score
from ..config import DEFAULT_LANG_IDS


@dataclass
class FontComparison:
    path: str
    digest: str
    size: int
    full_name: str = ''
    style: str = ''
    version: str = ''
    glyphs: int = 0
    characters: int = 0
    error: str = ''


def read_comparison(path):
    digest, size = fingerprint(path)
    result = FontComparison(str(Path(path).absolute()), digest, size)
    try:
        with open(path, 'rb') as stream, TTFont(stream, lazy=True) as font:
            records = sorted(font['name'].names, key=platform_score)
            def name(ids):
                for name_id in ids:
                    matches = [r for r in records if r.nameID == name_id]
                    for lang in DEFAULT_LANG_IDS:
                        for record in matches:
                            if record.langID == lang:
                                value = decode_name_record(record)
                                if value: return value
                    for record in matches:
                        value = decode_name_record(record)
                        if value: return value
                return ''
            result.full_name = name([4, 6])
            result.style = name([17, 2])
            result.version = name([5])
            result.glyphs = font['maxp'].numGlyphs if 'maxp' in font else 0
            result.characters = len(font.getBestCmap() or {}) if 'cmap' in font else 0
        if fingerprint(path) != (digest, size):
            raise ValueError('读取比较信息时文件变化，请重新扫描')
    except Exception as exc:
        result.error = str(exc)
    return result

"""字体比较信息：完整名称、字重样式、版本、字符覆盖。"""
from dataclasses import dataclass
from pathlib import Path
from .duplicates import fingerprint
from .reader import TTFont, decode_name_record, platform_score, select_font_name
from ..config import DEFAULT_LANG_IDS, DEFAULT_NAME_IDS


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
    rename_name: object = None
    stamp: tuple = ()


def read_comparison(path, name_ids=DEFAULT_NAME_IDS, lang_ids=DEFAULT_LANG_IDS, hash_content=True):
    before = Path(path).stat()
    digest, size = fingerprint(path) if hash_content else ("", before.st_size)
    result = FontComparison(str(Path(path).absolute()), digest, size)
    result.stamp = (before.st_size, before.st_mtime_ns, before.st_ino)
    try:
        with open(path, 'rb') as stream, TTFont(stream, lazy=True) as font:
            records = sorted(font['name'].names, key=platform_score) if 'name' in font else []
            result.rename_name = select_font_name(records, name_ids, lang_ids)
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
        after = Path(path).stat()
        if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
            raise ValueError('读取比较信息时文件变化，请重新扫描')
    except Exception as exc:
        result.error = str(exc)
    return result

from typing import Iterable, Optional
from .models import FontName

try:
    from fontTools.ttLib import TTFont, TTLibError
except Exception:  # GUI 启动后给出明确提示
    TTFont = None
    TTLibError = Exception


def decode_name_record(record) -> Optional[str]:
    """优先使用 fontTools 自带解码；失败时再尝试常见编码。"""
    for decoder in (
        lambda r: r.toUnicode(),
        lambda r: r.string.decode("utf-16be"),
        lambda r: r.string.decode("mac_roman"),
        lambda r: r.string.decode("utf-8", errors="ignore"),
    ):
        try:
            value = decoder(record)
            value = value.replace("\x00", "").strip()
            if value:
                return value
        except Exception:
            continue
    return None


def platform_score(record) -> int:
    """同一 NameID / LangID 下，优先 Windows Unicode，再考虑其他平台。"""
    if record.platformID == 3 and record.platEncID in (1, 10):
        return 0
    if record.platformID == 0:
        return 1
    if record.platformID == 1:
        return 2
    return 9


def get_font_name(font_path: str, name_ids: Iterable[int], lang_ids: Iterable[int]) -> Optional[FontName]:
    """按 NameID 与语言优先级读取字体名称。"""
    if TTFont is None:
        raise RuntimeError("缺少 fontTools。请先运行：pip install fonttools")

    try:
        with open(font_path, "rb") as stream, TTFont(stream, lazy=True) as font:
            name_table = font.get("name")
            if not name_table:
                return None

            records = sorted(name_table.names, key=platform_score)
            name_ids = list(name_ids)
            lang_ids = list(lang_ids)

            # 第一阶段：按用户语言优先级精确查找。
            for name_id in name_ids:
                for lang_id in lang_ids:
                    for record in records:
                        if record.nameID == name_id and record.langID == lang_id:
                            value = decode_name_record(record)
                            if value:
                                return FontName(value, name_id, lang_id, record.platformID)

            # 第二阶段：优先英文兜底。
            for fallback_lang_id in (0x0409, 0):
                for name_id in name_ids:
                    for record in records:
                        if record.nameID == name_id and record.langID == fallback_lang_id:
                            value = decode_name_record(record)
                            if value:
                                return FontName(value, name_id, fallback_lang_id, record.platformID)

            # 第三阶段：任何可解码名称兜底。
            for name_id in name_ids:
                for record in records:
                    if record.nameID == name_id:
                        value = decode_name_record(record)
                        if value:
                            return FontName(value, name_id, record.langID, record.platformID)

            return None
    except TTLibError as exc:
        raise RuntimeError(f"字体格式不支持或文件损坏：{exc}") from exc



"""Label generated headline pairs without changing manually entered copy."""
import json

from scene_tool.config.copy_phrases import SEPARATOR


def copy_instructions(copy):
    text = copy.strip() or '盛大开业 · 美好启幕'
    parts = text.split(SEPARATOR)
    if len(parts) == 2 and all(part.strip() for part in parts):
        headline, subline = (json.dumps(part.strip(), ensure_ascii=False) for part in parts)
        return [f'主文案：{headline}', f'副文案：{subline}',
                '主副文案分别排版，各出现一次；分隔符“｜”不印到板上。']
    return [f'开业文案：{json.dumps(text, ensure_ascii=False)}']

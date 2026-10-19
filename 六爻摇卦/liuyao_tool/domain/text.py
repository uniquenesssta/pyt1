"""将完整卦象转换为可粘贴的文字，排列顺序与界面一致。"""
from .yao import YAO_NAMES


def format_original(hexagram, name=""):
    rows = [f"本卦：{name}" if name else "本卦"]
    for index in range(5, -1, -1):
        line = hexagram.lines[index]
        state = "动爻" if line.is_changing else "静爻"
        rows.append(f"{YAO_NAMES[index]}：{line.symbol}  {line.name}（{line.value}）· {state}")
    return "\n".join(rows)


def format_changed(hexagram, name=""):
    state = "有变爻" if hexagram.has_changes else "无变爻"
    title = f"之卦：{name}（{state}）" if name else f"之卦（{state}）"
    rows = [title]
    for index in range(5, -1, -1):
        line = hexagram.lines[index]
        name = "阳爻" if line.changed_is_yang else "阴爻"
        rows.append(f"{YAO_NAMES[index]}：{line.changed_symbol}  {name}")
    return "\n".join(rows)

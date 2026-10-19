"""分别输出现代参考、原文资料；复制时一并保留依据和来源。"""


def format_reading(report):
    original, changed = report.original, report.changed
    moving = "、".join(str(line.position) for line in report.moving) or "无"
    rows = [
        f"本卦：{original.display_name}", f"之卦：{changed.display_name}",
        f"动爻（自下而上编号）：{moving}", "",
        "【问题与背景】", f"问题：{report.question or '未填写，以下为综合阅读。'}",
        f"背景：{report.background or '未填写，不补造具体情节。'}", "",
        "【原文依据】", f"本卦卦辞：{original.judgement}", f"本卦大象：{original.image}",
    ]
    for line in report.moving:
        rows.append(f"动爻第{line.position}爻 · {line.label}（{line.change}）：{line.text}")
    if not report.moving:
        rows.append("本轮没有动爻，本卦与之卦相同，以下围绕同一组卦辞展开阅读。")
    for line in report.special:
        rows.append(f"六爻皆动的补充原文 · {line.label}：{line.text}")
    if original.number != changed.number:
        rows.append(f"之卦卦辞：{changed.judgement}")

    rows.extend(("", "【参考解读 · 编辑概括与条件推测】",
                 f"本卦主题：{'、'.join(original.notes.keywords)}。{original.notes.summary}",
                 f"之卦主题：{'、'.join(changed.notes.keywords)}。{changed.notes.summary}",
                 "以下将之卦作为另一个观察角度，不视为已经确定的未来结果。"))
    for line in report.moving:
        rows.append(f"第{line.position}爻辅助提问〔编辑提示，非爻辞译文〕：{line.question}")
    for topic in report.topics:
        matching = "按问题或背景中的主题词辅助识别" if topic.keywords else "未匹配具体主题"
        rows.extend((
            "", f"主题匹配：{topic.name}〔{matching}〕",
            f"阅读焦点：{topic.focus}。",
            f"1. 推进角度：如果现实条件支持，可以从“{original.notes.opportunity}”这一方向对照问题。",
            f"2. 谨慎角度：如果现实中出现相关迹象，留意“{original.notes.caution}”这一可能。",
            f"3. 条件变化角度：若局面逐渐呈现“{'、'.join(changed.notes.keywords)}”，可检查“{changed.notes.opportunity}”是否适用；同时留意“{changed.notes.caution}”。",
            f"需要核实：{topic.check}",
        ))
    rows.extend(("", "【读法与边界】",
                 "原文是传统资料；主题概括、辅助提问和三个阅读角度由本工具编辑组织，不能作为原文的唯一解释。",
                 "第一版按卦象和主题词提供本地参考，未接入 AI，不推断未提供的事实、他人心理、应期或结果概率。",
                 "多动爻并列展示，不替你选定唯一取用爻。", "", "【原文来源】"))
    seen = set()
    for entry in (original, changed):
        if entry.number not in seen:
            rows.extend((entry.source_title, entry.source_revision_url))
            seen.add(entry.number)
    return "\n".join(rows)


def format_references(report):
    rows = ["《周易》原文资料", "保留来源中的繁体、异体字及注明的异文；以下原文与现代参考解读分别展示。", ""]
    seen = set()
    for role, entry in (("本卦", report.original), ("之卦", report.changed)):
        if entry.number in seen:
            rows.append("之卦与本卦相同，原文见上。")
            continue
        seen.add(entry.number)
        rows.extend((f"【{role} · {entry.display_name}】", f"下卦：{entry.lower}；上卦：{entry.upper}",
                     f"卦辞：{entry.judgement}", f"大象：{entry.image}", "爻辞（初爻至上爻）："))
        rows.extend(f"{line.label}：{line.text}" for line in entry.lines)
        rows.extend(f"{line.label}：{line.text}" for line in entry.special)
        rows.extend(("来源：" + entry.source_title, entry.source_revision_url, ""))
    return "\n".join(rows)

import os
from typing import Iterable
from ..config import STATUS_RENAME, STATUS_SKIP, STATUS_ERROR
from .models import RenamePlan
from .naming import normalize_path, sanitize_filename
from .reader import get_font_name

def iter_font_files(folder: str, extensions: Iterable[str], recursive: bool) -> list[str]:
    extensions = tuple(ext.lower() for ext in extensions)
    results: list[str] = []

    if recursive:
        for root, _, files in os.walk(folder):
            for file_name in files:
                if os.path.splitext(file_name)[1].lower() in extensions:
                    results.append(os.path.join(root, file_name))
    else:
        with os.scandir(folder) as entries:
            for entry in entries:
                if not entry.is_file():
                    continue
                if os.path.splitext(entry.name)[1].lower() in extensions:
                    results.append(entry.path)

    return sorted(results, key=lambda p: p.lower())


def build_rename_plan(
    folder: str,
    extensions: Iterable[str],
    name_ids: Iterable[int],
    lang_ids: Iterable[int],
    recursive: bool,
    duplicate_mode: str,
    lower_extension: bool,
    use_underscore: bool,
) -> list[RenamePlan]:
    font_files = iter_font_files(folder, extensions, recursive)
    plans: list[RenamePlan] = []

    # 记录已存在路径与本轮已占用目标路径，避免重名。
    existing_paths = {normalize_path(path) for path in font_files}
    reserved_targets: set[str] = set()

    for old_path in font_files:
        old_dir = os.path.dirname(old_path)
        old_base, old_ext = os.path.splitext(os.path.basename(old_path))
        new_ext = old_ext.lower() if lower_extension else old_ext

        try:
            font_name = get_font_name(old_path, name_ids, lang_ids)
            if not font_name:
                plans.append(RenamePlan(old_path, "", "", None, None, STATUS_SKIP, "无法从字体 name 表读取有效名称"))
                continue

            safe_base = sanitize_filename(font_name.text, use_underscore=use_underscore)
            target_name = f"{safe_base}{new_ext}"
            target_path = os.path.join(old_dir, target_name)

            old_norm = normalize_path(old_path)
            target_norm = normalize_path(target_path)

            # 完全相同则跳过；大小写或扩展名大小写不同，则仍允许改名。
            if old_path == target_path:
                plans.append(
                    RenamePlan(old_path, target_path, font_name.text, font_name.name_id, font_name.lang_id, STATUS_SKIP, "文件名已符合规则")
                )
                reserved_targets.add(target_norm)
                continue

            counter = 1
            original_target_name = target_name
            while True:
                target_norm = normalize_path(target_path)
                collides_with_existing = (target_norm in existing_paths or os.path.lexists(target_path)) and target_norm != old_norm
                collides_with_plan = target_norm in reserved_targets and target_norm != old_norm

                if not collides_with_existing and not collides_with_plan:
                    break

                if duplicate_mode == "跳过重名文件":
                    plans.append(
                        RenamePlan(old_path, target_path, font_name.text, font_name.name_id, font_name.lang_id, STATUS_SKIP, f"目标文件名已存在：{original_target_name}")
                    )
                    target_path = ""
                    break

                target_name = f"{safe_base}_{counter}{new_ext}"
                target_path = os.path.join(old_dir, target_name)
                counter += 1

            if not target_path:
                continue

            reserved_targets.add(normalize_path(target_path))
            reason = "按字体名称生成新文件名"
            if os.path.basename(target_path) != original_target_name:
                reason = f"目标重名，已自动添加后缀：{os.path.basename(target_path)}"

            plans.append(
                RenamePlan(old_path, target_path, font_name.text, font_name.name_id, font_name.lang_id, STATUS_RENAME, reason)
            )
        except Exception as exc:
            plans.append(RenamePlan(old_path, "", "", None, None, STATUS_ERROR, str(exc)))

    return plans



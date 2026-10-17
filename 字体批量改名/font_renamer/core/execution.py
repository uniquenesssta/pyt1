import os
import uuid
from ..config import STATUS_RENAME, STATUS_ERROR, STATUS_DONE
from .models import RenamePlan

def unique_temp_path(old_path: str) -> str:
    folder = os.path.dirname(old_path)
    name = os.path.basename(old_path)
    for _ in range(50):
        tmp_name = f".__font_rename_tmp_{uuid.uuid4().hex}"
        tmp_path = os.path.join(folder, tmp_name)
        if not os.path.exists(tmp_path):
            return tmp_path
    raise RuntimeError("无法生成临时文件名")


def execute_rename_plans(plans: list[RenamePlan], log_callback=None) -> tuple[int, int]:
    """两阶段改名：先 old -> 临时名，再 临时名 -> 目标名。"""
    todo = [p for p in plans if p.status == STATUS_RENAME and p.new_path]
    staged: list[tuple[RenamePlan, str]] = []
    success = 0
    failed = 0

    if not todo:
        return success, failed

    def log(text: str) -> None:
        if log_callback:
            log_callback(text)

    try:
        # 第一阶段：全部移动到临时名，避免相互覆盖、大小写改名失败等问题。
        for plan in todo:
            if not os.path.exists(plan.old_path):
                plan.status = STATUS_ERROR
                plan.reason = "原文件不存在，可能已被移动或删除"
                failed += 1
                continue

            tmp_path = unique_temp_path(plan.old_path)
            try:
                os.rename(plan.old_path, tmp_path)
                staged.append((plan, tmp_path))
                log(f"临时移动：{plan.old_name} -> {os.path.basename(tmp_path)}")
            except Exception as exc:
                plan.status = STATUS_ERROR
                plan.reason = f"移动到临时文件失败：{exc}"
                failed += 1

        # 第二阶段：临时名移动到最终目标名。
        for plan, tmp_path in staged:
            try:
                if os.path.lexists(plan.new_path):
                    raise FileExistsError(f"目标文件已存在：{plan.new_path}")
                os.rename(tmp_path, plan.new_path)
                plan.status = STATUS_DONE
                plan.reason = "已完成改名"
                success += 1
                log(f"成功：{plan.old_name} -> {plan.new_name}")
            except Exception as exc:
                plan.status = STATUS_ERROR
                plan.reason = f"改名到目标文件失败：{exc}"
                failed += 1
                # 尽量回滚当前失败项。
                try:
                    if os.path.exists(tmp_path) and not os.path.exists(plan.old_path):
                        os.rename(tmp_path, plan.old_path)
                        log(f"已回滚：{plan.old_name}")
                except Exception as rollback_exc:
                    plan.reason += f"；回滚也失败：{rollback_exc}"
                if os.path.lexists(tmp_path):
                    plan.reason += f"；文件保留在：{tmp_path}"
                    log(plan.reason)

    except Exception:
        # 理论上不应到这里；为了安全，尽量把仍处于临时名的文件回滚。
        for plan, tmp_path in staged:
            if os.path.exists(tmp_path) and not os.path.exists(plan.old_path):
                try:
                    os.rename(tmp_path, plan.old_path)
                except Exception:
                    pass
        raise

    return success, failed



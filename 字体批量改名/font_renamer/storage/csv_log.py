import os
import csv
import datetime as _dt
from ..core.models import RenamePlan

def write_csv_log(folder: str, plans: list[RenamePlan], prefix: str = "font_rename_log") -> str:
    timestamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    log_path = os.path.join(folder, f"{prefix}_{timestamp}.csv")

    with open(log_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["状态", "原路径", "新路径", "字体名称", "NameID", "LangID", "备注"])
        for p in plans:
            lang = f"0x{p.lang_id:04X}" if isinstance(p.lang_id, int) else ""
            writer.writerow([p.status, p.old_path, p.new_path, p.font_name, p.name_id if p.name_id is not None else "", lang, p.reason])

    return log_path



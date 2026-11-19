"""收藏表用北京时间标识，旧记录放在有时间的记录之后。"""
from ..core.favorites import newest_first
from .results import TicketPanel


UNDATED = "日期未记录"


class FavoritePanel(TicketPanel):
    def __init__(self, parent, status, error, remove):
        super().__init__(parent, "我的收藏", status, error, remove, "移除选中",
                         label_column="收藏时间（北京）", widths=(177, 543, 300))
        self.table.missing_sort_values[0] = UNDATED

    def set_favorites(self, records):
        ordered = newest_first(records)
        self.set_tickets((record.ticket for record in ordered), labels=(
            record.saved_at.strftime("%Y-%m-%d %H:%M:%S") if record.saved_at else UNDATED
            for record in ordered
        ))
        self.table.mark_sort(0, True)

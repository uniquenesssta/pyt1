"""识别开奖报表列布局；仅在明确表头下提取号码，不猜奖金列。"""
from dataclasses import dataclass


@dataclass(frozen=True)
class DrawColumns:
    issue: int
    front: tuple
    back: tuple

    def extract(self, cells):
        indexes = (self.issue,) + self.front + self.back
        if len(cells) <= max(indexes):
            raise ValueError('开奖列缺失，记录不完整')
        values = [cells[i] for i in indexes]
        if any(not value for value in values):
            raise ValueError('期号或开奖号码单元格为空')
        return values


def detect_columns(cells):
    """支持期号、日期、前区5列、后区2列的开奖报表。"""
    normalized = [''.join(c.split()) for c in cells]
    for start, label in enumerate(normalized):
        if label not in ('开奖期号', '期号') or len(cells) < start + 9:
            continue
        if normalized[start + 1] not in ('开奖日期', '日期'):
            continue
        front = normalized[start + 2:start + 7]
        back = normalized[start + 7:start + 9]
        split_labels = front == ['前', '区', '', '', ''] and back == ['后', '区']
        merged_labels = front == ['前区', '', '', '', ''] and back == ['后区', '']
        numbered_labels = front == [f'前区{i}' for i in range(1, 6)] and back == ['后区1', '后区2']
        if split_labels or merged_labels or numbered_labels:
            return DrawColumns(start, tuple(range(start + 2, start + 7)), tuple(range(start + 7, start + 9)))
    return None

"""历史数据快照：一次原子写入，启动时离线恢复。"""
import json
from datetime import datetime
from pathlib import Path
from dataclasses import asdict
from ..core.models import Draw, Ticket
from .importing import Dataset, ImportIssue
from .storage import atomic_write


class HistoryStore:
    def __init__(self, path):
        self.path = Path(path)

    def save(self, dataset):
        payload = {'version': 1, 'saved_at': datetime.now().isoformat(timespec='seconds'),
                   'dataset': asdict(dataset)}
        atomic_write(self.path, json.dumps(payload, ensure_ascii=False))

    def load(self):
        if not self.path.exists():
            return None
        try:
            payload = json.loads(self.path.read_text(encoding='utf-8'))
            if payload['version'] != 1:
                raise ValueError('不支持的历史快照版本')
            data = payload['dataset']
            data['draws'] = [Draw(Ticket(tuple(d['ticket']['front']), tuple(d['ticket']['back'])),
                                  d['issue'], d['line'], d.get('sheet', '')) for d in data['draws']]
            data['issues'] = [ImportIssue(**item) for item in data['issues']]
            result = Dataset(**data)
            if not result.draws:
                raise ValueError('历史快照为空')
            return result
        except (ValueError, KeyError, TypeError, AttributeError) as exc:
            raise ValueError(f'历史快照无法读取，原文件保留；可重新导入或更新：{exc}') from exc

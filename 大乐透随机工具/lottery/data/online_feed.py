"""乐彩网开奖文本下载与校验，不依赖 Excel 或执行宏。"""
from datetime import date
import re
import time
from urllib.request import Request, urlopen
from ..core.models import check_cancel
from .importing import Dataset, parse_line

FEED_URL = 'http://www.17500.cn/getData/dlt.TXT'
MAX_BYTES = 8_000_000


def download(cancel=None, progress=None):
    request = Request(FEED_URL, headers={'User-Agent': 'LotteryHistoryTool/1.0', 'Accept': 'text/plain'})
    started = time.monotonic()
    chunks, total = [], 0
    check_cancel(cancel)
    with urlopen(request, timeout=15) as response:
        if response.status != 200:
            raise ValueError(f'数据源返回 HTTP {response.status}')
        while True:
            check_cancel(cancel)
            if time.monotonic() - started > 45:
                raise TimeoutError('下载超时，请稍后重试')
            chunk = response.read(65536)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_BYTES:
                raise ValueError('下载文件异常过大，已停止更新')
            chunks.append(chunk)
            if progress:
                progress(f'正在下载开奖数据：{total // 1024:,} KB')
    check_cancel(cancel)
    return b''.join(chunks)


def parse_feed(raw, cancel=None):
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        text = raw.decode('gb18030')
    result = Dataset(source=FEED_URL, encoding='在线开奖文本')
    seen = {}
    for number, line in enumerate(text.splitlines(), 1):
        check_cancel(cancel)
        if not line.strip():
            continue
        cells = line.split()
        try:
            if len(cells) < 9 or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', cells[1]):
                raise ValueError('缺少期号、日期或 5+2 号码')
            date.fromisoformat(cells[1])
            draw = parse_line(' '.join([cells[0]] + cells[2:9]), number)
            if draw.issue in seen:
                if seen[draw.issue] != draw.ticket:
                    raise ValueError(f'同一期 {draw.issue} 存在不同号码')
                result.duplicates += 1
                continue
            seen[draw.issue] = draw.ticket
            result.draws.append(draw)
        except ValueError as exc:
            raise ValueError(f'在线数据第 {number} 行异常：{exc}；原数据保留') from exc
    if not result.draws:
        raise ValueError('在线文件没有有效开奖数据，原数据保留')
    result.draws.sort(key=lambda d: int(d.issue))
    return result


def validate_update(incoming, previous):
    """全量源不得丢期或静默改号；新增期按期号计数。"""
    current = {d.issue: d.ticket for d in incoming.draws}
    old = {}
    if previous is not None:
        for draw in previous.draws:
            if not draw.issue:
                continue
            if draw.issue in old and old[draw.issue] != draw.ticket:
                raise ValueError(f'本地第 {draw.issue} 期有冲突，请先核对')
            old[draw.issue] = draw.ticket
    missing = old.keys() - current.keys()
    if missing:
        raise ValueError(f'下载数据缺少本地已有的 {len(missing)} 期，原数据保留')
    conflicts = [issue for issue in old if old[issue] != current[issue]]
    if conflicts:
        raise ValueError(f'第 {conflicts[0]} 期与本地号码不同，请核对来源；原数据保留')
    return len(current.keys() - old.keys())

"""固定十线程读取：按完成数报告进度，按输入顺序返回结果。"""
from concurrent.futures import ThreadPoolExecutor, as_completed

READ_WORKERS = 10


def parallel_read(items, reader, progress=None):
    """每项返回 (结果, 异常)，单个文件失败不打断其他读取。"""
    results = [None] * len(items)
    if not items:
        return results
    with ThreadPoolExecutor(max_workers=READ_WORKERS, thread_name_prefix='font-read') as pool:
        futures = {pool.submit(reader, item): index for index, item in enumerate(items)}
        for completed, future in enumerate(as_completed(futures), 1):
            index = futures[future]
            try:
                results[index] = (future.result(), None)
            except Exception as exc:
                results[index] = (None, exc)
            if progress and (completed == 1 or completed % 50 == 0 or completed == len(items)):
                progress(completed, len(items))
    return results

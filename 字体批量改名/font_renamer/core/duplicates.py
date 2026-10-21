"""按字节内容扫描重复文件，并在清理前重新校验。"""
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
from .planning import iter_font_files


@dataclass
class Duplicate:
    keep: str
    path: str
    digest: str
    size: int
    status: str = '待清理'
    reason: str = ''


def fingerprint(path):
    p = Path(path)
    if p.is_symlink() or not p.is_file():
        raise ValueError('文件不存在或为符号链接')
    before = p.stat()
    h = hashlib.sha256()
    with p.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    after = p.stat()
    if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
        raise ValueError('读取期间文件发生变化，请重新扫描')
    return h.hexdigest(), after.st_size


def scan_duplicates(folder, extensions, recursive):
    sizes = {}
    errors = []
    for path in iter_font_files(folder, extensions, recursive):
        try:
            if Path(path).is_symlink():
                continue
            sizes.setdefault(os.path.getsize(path), []).append(os.path.abspath(path))
        except OSError as exc:
            errors.append(f'{path}: {exc}')
    results = []
    for size, paths in sizes.items():
        if len(paths) < 2:
            continue
        seen = {}
        for path in sorted(paths, key=lambda p: (p.casefold(), p)):
            try:
                digest, actual_size = fingerprint(path)
                if actual_size != size:
                    raise ValueError('文件大小已改变，请重新扫描')
                if digest in seen:
                    keep = seen[digest]
                    if not os.path.samefile(keep, path):
                        results.append(Duplicate(keep, path, digest, size))
                else:
                    seen[digest] = path
            except Exception as exc:
                errors.append(f'{path}: {exc}')
    return results, errors


def clean_duplicates(items, recycle):
    success = 0
    for item in items:
        if item.status != '待清理':
            continue
        try:
            expected = (item.digest, item.size)
            if fingerprint(item.keep) != expected or fingerprint(item.path) != expected:
                raise ValueError('保留文件或重复文件已改变，请重新扫描')
            if os.path.samefile(item.keep, item.path):
                raise ValueError('指向同一个文件，不清理')
            recycle(item.path)
            item.status = '已移入回收站'
            success += 1
        except Exception as exc:
            item.status = '失败'
            item.reason = str(exc)
    return success

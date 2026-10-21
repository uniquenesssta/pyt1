"""同名候选分组及用户指定保留项后的清理。"""
from dataclasses import dataclass, field
from pathlib import Path
import os
import unicodedata
from .planning import iter_font_files
from .font_comparison import read_comparison
from .duplicates import fingerprint


@dataclass
class NameGroup:
    members: list
    keep: str = ''
    status: str = '待选择保留项'
    details: list = field(default_factory=list)


def name_key(text):
    return unicodedata.normalize('NFKC', text).strip().casefold()


def scan_same_names(folder, extensions, recursive):
    entries, errors = [], []
    identities = set()
    for path in iter_font_files(folder, extensions, recursive):
        try:
            p = Path(path)
            if p.is_symlink(): continue
            st = p.stat()
            identity = (st.st_dev, st.st_ino)
            if st.st_ino and identity in identities: continue
            identities.add(identity)
            info = read_comparison(path)
            entries.append(info)
            if info.error: errors.append(f'{path}: {info.error}')
        except Exception as exc:
            errors.append(f'{path}: {exc}')
    # 合并共享文件名或内部完整名称的候选，避免一个文件出现在多个清理组。
    parents = list(range(len(entries)))
    def root(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i
    seen = {}
    for i, item in enumerate(entries):
        keys = [('filename',name_key(Path(item.path).stem))]
        if item.full_name and not item.error:
            keys.append(('fontname',name_key(item.full_name)))
        for key in keys:
            if key in seen: parents[root(i)] = root(seen[key])
            else: seen[key] = i
    groups = {}
    for i, item in enumerate(entries): groups.setdefault(root(i),[]).append(item)
    return [NameGroup(items) for items in groups.values() if len(items)>1], errors


def clean_name_groups(groups, recycle):
    success = 0
    for group in groups:
        if not group.keep or group.status != '待清理': continue
        keep = next((m for m in group.members if m.path == group.keep), None)
        if keep is None:
            group.status = '失败'; group.details.append('保留项无效'); continue
        group.details = []
        for item in group.members:
            if item.path == keep.path: continue
            try:
                if fingerprint(keep.path) != (keep.digest,keep.size):
                    raise ValueError('保留文件改变或丢失，请重新扫描')
                if fingerprint(item.path) != (item.digest,item.size):
                    raise ValueError('待清理文件改变，请重新扫描')
                if os.path.samefile(keep.path,item.path):
                    raise ValueError('指向同一文件，不清理')
                recycle(item.path)
                success += 1
                group.details.append(f'已移入回收站：{item.path}')
            except Exception as exc:
                group.details.append(f'失败：{item.path}：{exc}')
        group.status = '有失败，请重新扫描' if any(s.startswith('失败') for s in group.details) else '清理完成'
    return success

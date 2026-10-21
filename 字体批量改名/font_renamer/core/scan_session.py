"""一次目录扫描与字体解析，供改名、重复及同名窗口共用。"""
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from .planning import iter_font_files, build_rename_plan
from .font_comparison import read_comparison
from .same_names import group_same_names
from .duplicates import fingerprint, Duplicate


@dataclass
class ScanSession:
    plans: list
    duplicates: list
    name_groups: list
    errors: list


def scan_session(config, progress=None):
    paths = iter_font_files(config['folder'],config['extensions'],config['recursive'])
    lookup, entries, errors = {}, [], []
    identities = set()
    for index,path in enumerate(paths):
        try:
            if Path(path).is_symlink(): raise ValueError('跳过符号链接')
            info = read_comparison(path, config['name_ids'], config['lang_ids'], hash_content=False)
            lookup[path] = info
            stat = Path(path).stat()
            identity = (stat.st_dev,stat.st_ino)
            if not stat.st_ino or identity not in identities: entries.append(info)
            identities.add(identity)
            if info.error: errors.append(f'{path}: {info.error}')
        except Exception as exc:
            lookup[path] = exc; errors.append(f'{path}: {exc}')
        if progress and (index % 50 == 0 or index+1 == len(paths)):
            progress(f'读取字体信息 {index+1}/{len(paths)}')
    groups = group_same_names(entries)
    named = {m.path for g in groups for m in g.members}
    counts = Counter(m.size for m in entries)
    candidates = [m for m in entries if counts[m.size]>1 or m.path in named]
    for index,m in enumerate(candidates):
        try:
            stat = Path(m.path).stat()
            if (stat.st_size,stat.st_mtime_ns,stat.st_ino) != m.stamp:
                raise ValueError("字体信息读取后文件发生变化，请重新扫描")
            m.digest,size = fingerprint(m.path)
            if size != m.size: raise ValueError('扫描期间大小变化，请重新扫描')
        except Exception as exc:
            m.digest=''; errors.append(f'{m.path}: {exc}')
        if progress and (index % 50 == 0 or index+1 == len(candidates)):
            progress(f'校验重复候选 {index+1}/{len(candidates)}')
    groups = [g for g in groups if all(m.digest for m in g.members)]
    seen, duplicates = {}, []
    for m in sorted(entries,key=lambda m:(m.path.casefold(),m.path)):
        if not m.digest: continue
        if m.digest in seen:
            duplicates.append(Duplicate(seen[m.digest].path,m.path,m.digest,m.size))
        else: seen[m.digest]=m
    def name_lookup(path):
        value=lookup[path]
        if isinstance(value,Exception): raise value
        if value.error and not value.rename_name: raise ValueError(value.error)
        return value.rename_name
    plans=build_rename_plan(**config,font_files=paths,name_lookup=name_lookup)
    return ScanSession(plans,duplicates,groups,errors)

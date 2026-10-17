"""Independent parameter sampling and prompt composition; Python standard library only."""
from __future__ import annotations

import json
import os
from pathlib import Path
import random
import tempfile

from generators import fresh_value

DIMENSIONS = (
    ('logo_shape', 'Logo 图形形态'), ('logo_structure', 'Logo 视觉结构'),
    ('brand', '品牌名称'), ('city', '地理位置'), ('address', '街道地址'),
    ('architecture', '门店建筑风格'), ('placement', 'KT板布置位置'),
    ('balloons', '气球造型'), ('camera', '拍摄角度'),
    ('lighting', '天气及光线'), ('ratio', '画面比例'),
)
INDUSTRIES = ('美业', '服装', '咖啡', '餐饮', '花店', '家居', '通用 / 自定义')
DEFAULT_CONSTRAINTS = '''根据我上传的参考图，生成一张全新的商业开业真实手机摄影效果图（photorealism）。
横版KT板固定为3.5米宽、2.2米高，必须有真实的大型板材尺度感，不是小型招牌；拍摄画面比例与板材本身比例分别执行。
严格保留原图背景图案、波浪线条和紫色渐变配色，仅替换Logo图形、品牌名称、开业文案、地址，允许为新文字合理调整文字排版。
紫白气球颜色保持一致，真实、略微通透，柔和自然高光，不能过亮、塑料般耀眼。
创建全新的门店环境与布局；建筑、摆板位置、装饰轮廓、拍摄视角必须按当前参数执行，不得套用上一张构图。
避免默认莲花Logo、正中摆板、对称气球拱门和固定玻璃门头的套路。
板面干净、字形清晰，中文准确；环境透视、板材支撑和气球固定方式符合现实，保留轻微手持手机拍摄感。'''


def validate_pools(value):
    if not isinstance(value, dict):
        raise ValueError('参数池必须是 JSON 对象。')
    result = {}
    for key, label in DIMENSIONS:
        items = value.get(key)
        if not isinstance(items, list) or not all(isinstance(x, str) and x.strip() for x in items):
            raise ValueError(f'{label}：必须是非空字符串列表。')
        items = list(dict.fromkeys(x.strip() for x in items))
        if len(items) < 2:
            raise ValueError(f'{label}：至少保留两个不同选项。')
        result[key] = items
    return result


def upgrade_pools(pools, defaults, legacy):
    """Upgrade untouched v1 pools, while preserving genuinely customized lists."""
    result = dict(pools)
    for key, previous in legacy.items():
        if result.get(key) == previous:
            result[key] = list(defaults[key])
    return validate_pools(result)


def load_pools(path):
    return validate_pools(json.loads(Path(path).read_text(encoding='utf-8')))


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    name = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                         suffix='.tmp', delete=False) as f:
            name = f.name
            json.dump(value, f, ensure_ascii=False, indent=2)
        os.replace(name, path)
    finally:
        if name and os.path.exists(name):
            os.unlink(name)


class Randomizer:
    """Each dimension has its own shuffle bag. Locks never consume bag entries.

    Strong mode exhausts every option before refilling; both modes avoid the
    immediately previous value. No shared index ties dimensions together.
    """
    def __init__(self, pools, rng=None, generated=True):
        self.pools = validate_pools(pools)
        self.rng = rng or random.SystemRandom()
        self.bags = {}
        self.generated = generated
        self.recent = {"brand": [], "address": []}

    def restore_bags(self, bags):
        if not isinstance(bags, dict):
            return
        for key, items in bags.items():
            if key in self.pools and isinstance(items, list):
                self.bags[key] = list(dict.fromkeys(x for x in items
                    if isinstance(x, str) and x in self.pools[key]))

    def restore_recent(self, recent):
        if isinstance(recent, dict):
            for key in self.recent:
                items = recent.get(key, [])
                if isinstance(items, list):
                    self.recent[key] = [x for x in items if isinstance(x, str)][-200:]

    def draw(self, current=None, locked=(), strong=True):
        current = current or {}
        result = dict(current)
        for key, _ in DIMENSIONS:
            if key in locked and current.get(key, '').strip():
                continue
            previous = current.get(key)
            if self.generated and key in self.recent:
                value = fresh_value(key, self.rng, previous, self.recent[key])
                self.recent[key] = (self.recent[key] + [value])[-200:]
                result[key] = value
                continue
            if not strong:
                result[key] = self.rng.choice([x for x in self.pools[key] if x != previous])
                continue
            bag = self.bags.setdefault(key, [])
            if not bag:
                bag.extend(self.pools[key])
                self.rng.shuffle(bag)
            candidates = [x for x in bag if x != previous]
            if not candidates:
                # A manual edit may equal the final remaining entry. Begin a new
                # cycle to prioritize never repeating the value currently shown.
                bag[:] = self.pools[key]
                self.rng.shuffle(bag)
                candidates = [x for x in bag if x != previous]
            selected = self.rng.choice(candidates)
            bag.remove(selected)
            result[key] = selected
        return result


def make_prompt(values, industry='美业', constraints=DEFAULT_CONSTRAINTS,
                copy='盛大开业 · 美好启幕', extra=''):
    missing = [label for key, label in DIMENSIONS if not values.get(key, '').strip()]
    if missing:
        raise ValueError('请填写：' + '、'.join(missing))
    lines = [constraints.strip(), '', f'本轮行业：{industry.strip() or "通用"}',
             f'开业文案：{copy.strip() or "盛大开业 · 美好启幕"}', '',
             '以下11维参数已分别抽取，必须逐项执行，不得擅自换成惯用组合：']
    lines.extend(f'{label}：{values[key].strip()}' for key, label in DIMENSIONS)
    if extra.strip():
        lines.extend(['', '补充要求：', extra.strip()])
    lines.extend(['', '参考图由我随本指令一并上传。请直接生成图片，不要只复述参数。'])
    return '\n'.join(lines)

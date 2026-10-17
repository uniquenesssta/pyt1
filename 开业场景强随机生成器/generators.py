"""Offline coined names with paired phonetic syllables, and fictional addresses."""
SYLLABLES = (
    ('LU', '露'), ('MI', '米'), ('NA', '娜'), ('LI', '莉'),
    ('LA', '拉'), ('NU', '努'), ('MO', '莫'), ('MA', '玛'),
    ('NI', '妮'), ('NO', '诺'), ('LE', '乐'), ('LO', '洛'),
    ('SU', '苏'), ('SA', '莎'), ('SI', '希'), ('SO', '索'),
    ('RU', '茹'), ('RA', '拉'), ('RI', '莉'), ('RO', '若'),
    ('VE', '薇'), ('VI', '维'), ('VA', '瓦'), ('VO', '沃'),
    ('FA', '法'), ('FI', '菲'), ('FU', '芙'), ('FE', '斐'),
    ('DA', '达'), ('DI', '迪'), ('DO', '朵'), ('DU', '杜'),
)
STREET_FIRST = tuple('云 星 月 花 青 晴 南 北 东 西 春 夏 秋 冬 松 竹 兰 梅 桃 柳 溪 湖 海 江 山 林 锦 玉 银 金 清 明 安 宁 长 新 望 听 映 沐'.split())
STREET_SECOND = tuple('栖 悦 禾 岚 川 庭 鹭 序 澜 光 夏 影 舒 棠 汀 岸 源 桥 溪 泉 湾 岭 谷 园 华 和 丰 景 辰 晖 露 霖 晓 远 逸 然 知 语 歌 梦'.split())
STREET_TYPES = ('路', '街', '巷', '大道')


def brand_from_parts(parts):
    """Use the same sampled syllables for both scripts; never draw them separately."""
    return ''.join(western for western, _ in parts) + ' ' + ''.join(chinese for _, chinese in parts)


def generate_brand(rng):
    # Two or three distinct syllables, each with a fixed Chinese reading.
    return brand_from_parts(rng.sample(SYLLABLES, rng.choice((2, 3))))


def generate_address(rng):
    return f'{rng.choice(STREET_FIRST)}{rng.choice(STREET_SECOND)}{rng.choice(STREET_TYPES)} {rng.randint(1, 999)} 号'


def fresh_value(key, rng, previous, recent):
    factory = generate_brand if key == 'brand' else generate_address
    excluded = set(recent)
    excluded.add(previous)
    for _ in range(1000):
        value = factory(rng)
        if value not in excluded:
            return value
    raise ValueError('暂未抽到新组合，请重试。')

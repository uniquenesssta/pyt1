"""Generate drafts on isolated engines; opening content stays the same in a batch."""
import copy
import random
from scene_tool.config.closeup import CLOSEUP
from scene_tool.config.product_size import FOLLOW_REFERENCE
from scene_tool.config.studio_shots import camera_family
from scene_tool.domain.prompts import make_prompt
from scene_tool.domain.visibility import hidden_keys
from scene_tool.domain.variants.selection import Variant, select_variants

def clone_rng(rng):
    return random.SystemRandom() if isinstance(rng, random.SystemRandom) else copy.deepcopy(rng)

def clone_engine(engine):
    result = copy.copy(engine)
    for key, value in vars(engine).items():
        if key == 'rng':
            result.rng = clone_rng(value)
        else:
            setattr(result, key, copy.deepcopy(value))
    return result


def features(values, style, hidden, mapping=None):
    mapping = mapping or {k:k for k in values}
    canonical = {mapping.get(k,k):v for k,v in values.items() if k not in hidden}
    names = {'camera':'机位','detail_crop':'构图','detail_focus':'焦点',
             'detail_light':'光线','detail_reflection':'反光','architecture':'空间',
             'placement':'摆位','lighting':'光线','balloons':'气球','environment':'场地'}
    if style != CLOSEUP:
        for k in canonical:
            if k.endswith('_0'): names[k]='空间'
            elif k.endswith('_2'): names[k]='摆位'
            elif k.endswith('_5'): names[k]='构图'
            elif k=='time': names[k]='光线'
    result = {}
    if 'camera' in canonical and style == CLOSEUP:
        result['镜头类别'] = camera_family(canonical['camera']) or '自定义机位'
    for k,v in canonical.items():
        if k in names:
            result[names[k]] = v.split('；',1)[0]
    # Other visible changes still count when the main fields are locked.
    for k,v in canonical.items():
        if k not in names and k not in ('close_subject','close_material','brand','logo_shape','logo_structure'):
            result[k] = v
    return result


def opening_variants(engine, values, locks, *, style, industry, constraints, copyline,
                     extra='', hidden=(), product_size=FOLLOW_REFERENCE, strong=True,
                     generated=None):
    sandbox = clone_engine(engine)
    if generated is not None:
        sandbox.generated = generated
    current = dict(values)
    # Four photographic alternatives for the same design and format.
    locked = set(locks) | {k for k in ('brand','logo_shape','logo_structure','ratio') if current.get(k)}
    # A locked interior layout/camera must not be carried into an outdoor draft.
    if style != CLOSEUP and locked.intersection(('architecture','placement','balloons','camera')):
        locked.add('environment')
    hidden = hidden_keys(hidden)
    candidates = []
    for _ in range(48):
        current = sandbox.draw(current, locked, strong, style, industry, preserve_locked=True)
        locked.update(k for k in ('brand','logo_shape','logo_structure','ratio') if current.get(k))
        prompt = make_prompt(current,industry,constraints,copyline,extra,hidden,style,product_size)
        candidates.append(Variant(prompt,features(current,style,hidden),
                          {'values':dict(current), 'engine':clone_engine(sandbox)}))
    return select_variants(candidates)


def scene_variants(model):
    sandbox = clone_engine(model)
    if sandbox.values.get('ratio'):
        sandbox.locks['ratio'] = True
    hidden = hidden_keys(sandbox.hidden)
    mapping = {d['key']:d.get('close_key',d['key']) for d in sandbox.active_profile()['dimensions']}
    candidates = []
    for _ in range(48):
        sandbox.draw(preserve_locked=True)
        if sandbox.values.get('ratio'):
            sandbox.locks['ratio'] = True
        candidates.append(Variant(sandbox.generate(),features(sandbox.values,sandbox.render_style,hidden,mapping),
                                  {'values':dict(sandbox.values),'bags':copy.deepcopy(sandbox.bags),
                                   'rng':clone_rng(sandbox.rng)}))
    return select_variants(candidates)

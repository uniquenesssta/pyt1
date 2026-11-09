"""Version-compatible material presets; legacy descriptions acquire no inferred finish."""
from scene_tool.config.paths import DATA
from scene_tool.config.material_finish import FOLLOW, normalize
from scene_tool.storage.json_files import load_json, atomic_json

PATH = DATA / 'material_presets.json'


def record(value):
    if isinstance(value,str): value={'description':value,'finish':FOLLOW}
    if not isinstance(value,dict) or set(value)-{'description','finish'}:
        raise ValueError('材质预设格式错误，未覆盖原文件。')
    description=value.get('description')
    if not isinstance(description,str) or not description.strip():
        raise ValueError('请填写自定义材质。')
    return {'description':description.strip(),'finish':normalize(value.get('finish'))}


def load(path=None):
    path=path or PATH
    if not path.exists(): return {}
    data=load_json(path)
    if not isinstance(data,dict) or any(not isinstance(k,str) or not k.strip() for k in data):
        raise ValueError('材质预设文件格式错误，未覆盖原文件。')
    return {k:record(v) for k,v in data.items()}


def save(name,description,path=None,*,finish=FOLLOW):
    name=name.strip()
    if not name: raise ValueError('请填写预设名称。')
    if len(name)>64: raise ValueError('预设名称请控制在64字以内。')
    value=record({'description':description,'finish':finish})
    path=path or PATH
    data=load(path)
    data[name]=value
    atomic_json(path,data)
    return data


def delete(name,path=None):
    path=path or PATH
    data=load(path)
    data.pop(name,None)
    atomic_json(path,data)
    return data

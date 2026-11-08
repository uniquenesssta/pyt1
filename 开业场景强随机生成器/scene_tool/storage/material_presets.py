"""User-authored material descriptions shared by all scenes in this tool."""
from scene_tool.config.paths import DATA
from scene_tool.storage.json_files import load_json, atomic_json

PATH = DATA / 'material_presets.json'

def load(path=None):
    path = path or PATH
    if not path.exists(): return {}
    data = load_json(path)
    if not isinstance(data,dict) or any(not isinstance(k,str) or not k.strip() or
        not isinstance(v,str) or not v.strip() for k,v in data.items()):
        raise ValueError('材质预设文件格式错误，未覆盖原文件。')
    return data

def save(name, description, path=None):
    name,description = name.strip(),description.strip()
    if not name or not description:
        raise ValueError('请填写预设名称和自定义材质。')
    if len(name)>64: raise ValueError('预设名称请控制在64字以内。')
    path=path or PATH
    data=load(path)
    data[name]=description
    atomic_json(path,data)
    return data

def delete(name,path=None):
    path=path or PATH
    data=load(path)
    data.pop(name,None)
    atomic_json(path,data)
    return data


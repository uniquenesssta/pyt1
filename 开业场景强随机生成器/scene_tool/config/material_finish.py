"""Explicit product finish; never inferred from a free-text material name."""
from scene_tool.config import surface_reflection as reflection

KEY = 'close_finish'
FOLLOW, MATTE, SOFT, GLOSS = OPTIONS = ('跟随参考', '哑光', '微光', '亮面')
ALLOWED = {
    MATTE: (reflection.AUTO, reflection.MATTE),
    SOFT: (reflection.AUTO, reflection.SOFT),
    GLOSS: (reflection.AUTO, reflection.SOFT, reflection.GLOSS, reflection.HIGH),
}

def normalize(value):
    if value in (None, ''): return FOLLOW
    if value not in OPTIONS: raise ValueError('材质表面请选择跟随参考、哑光、微光或亮面。')
    return value

def effective(finish, strength):
    finish=normalize(finish)
    return finish if finish!=FOLLOW and strength==reflection.AUTO else strength


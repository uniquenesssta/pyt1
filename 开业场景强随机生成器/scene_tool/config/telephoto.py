"""Front-facing telephoto choices shared by all scene catalogs."""
TELEPHOTO_ANGLES = [
    f'正面平视，等效{focal}mm长焦，手持手机后置长焦镜头，镜头朝向KT板正面；后退到足够距离容纳完整装置，不裁切主体、不使用超广角、不刻意虚化'
    for focal in (75, 85, 100, 120, 135, 150)
]

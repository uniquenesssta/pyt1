"""Camera candidates for commercial images and indoor handheld photographs."""
COMMERCIAL_ANGLES = tuple(
    f'{angle}，等效{focal}mm长焦；相机保持水平、竖线端正，后退至装置完整入镜，文字清晰，不使用广角'
    for focal in (75, 85, 100, 120, 135, 150)
    for angle in ('正面平视，成像平面与板面平行', '左前方10度平视', '左前方20度平视',
                  '左前方30度平视', '右前方10度平视', '右前方20度平视', '右前方30度平视')
)
INDOOR_ANGLES = tuple(
    f'{angle}；{position}，手机自然持于{height}，使用后置主摄1倍；装置完整入镜，保持室内真实尺度，不穿墙、不站上家具、不使用超广角'
    for angle in ('正面平视', '左前方约10度平视', '左前方约20度平视', '右前方约10度平视', '右前方约20度平视')
    for position in ('站在室内可通行区域', '沿家具外侧通道后退取景', '在室内门边空位朝房间内取景', '在房间对侧空位取景')
    for height in ('胸口高度并保持镜头水平', '眼睛高度')
)

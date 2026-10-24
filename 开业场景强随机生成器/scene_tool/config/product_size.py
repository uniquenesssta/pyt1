"""Product geometry is independent of the photograph aspect ratio."""
FOLLOW_REFERENCE = '跟随参考图产品比例'
FIXED_LARGE = '固定尺寸：3.5米×2.2米'
PRODUCT_SIZE_CHOICES = (FOLLOW_REFERENCE, FIXED_LARGE, '固定比例：1:1', '固定比例：4:3', '固定比例：16:9')


def normalize_size(value, default=FOLLOW_REFERENCE):
    return value.strip() if isinstance(value, str) and value.strip() else default

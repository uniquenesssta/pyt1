"""Physical product dimensions; photograph aspect ratio is configured elsewhere."""
FOLLOW_REFERENCE = '参考图尺寸（未标注则不指定）'
FIXED_LARGE = '固定尺寸：3.5米×2.2米'
PRODUCT_SIZE_CHOICES = (FOLLOW_REFERENCE, FIXED_LARGE)


def normalize_size(value, default=FOLLOW_REFERENCE):
    if not isinstance(value, str) or not value.strip():
        return default
    if value == '跟随参考图产品比例' or value.startswith('固定比例：'):
        return FOLLOW_REFERENCE
    return value.strip()

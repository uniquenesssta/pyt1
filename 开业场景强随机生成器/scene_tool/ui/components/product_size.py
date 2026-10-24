"""Two product-size presets shared by every scene."""
from scene_tool.config.product_size import PRODUCT_SIZE_CHOICES, normalize_size


def product_size_row(results, variable):
    variable.set(normalize_size(variable.get()))
    return results.result('产品尺寸', variable, None,
                          choices=PRODUCT_SIZE_CHOICES, readonly=True)

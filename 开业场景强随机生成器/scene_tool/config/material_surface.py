"""Describe the visible face of a product at the selected framing distance."""

SURFACE_OPTIONS = ('保持原有底色', '呈现轮廓与底色的交界', '保持已有细节清楚', '保留真实明暗过渡')
OLD_SURFACES = {'保留原有色泽与纹理': SURFACE_OPTIONS[0],
                '保留表面细微质感，不锐化造边': SURFACE_OPTIONS[2]}


def material_brief(value):
    value = (value or '').strip().rstrip('。；; ')
    if not value:
        return '材质按参考图可见特征表现，不推测未指定的材质或工艺。'
    if '写真布' not in value:
        return f'指定材质：{value}。按描述和实物参考呈现，不增加其他工艺。'
    # Preserve bespoke finish/texture descriptions. Only bare stock names need a default.
    stock = value in {'写真布', '写真布背胶', '背胶写真布', '喷绘写真布', '喷绘写真布成品', '背胶喷绘写真布'}
    face = ('此距离下印刷正面平整，分辨不出织纹。' if stock else '')
    return (f'指定材质：{value}。{face}焦点落在印刷图文，边缘按实物裁切，不添加缝边。'
            '色彩与工艺以原稿和指定材质为准，不额外添加金属效果。')

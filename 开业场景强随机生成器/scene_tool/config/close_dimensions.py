"""Shared vocabulary for photographing an existing product rather than redesigning it."""
from scene_tool.config.closeup import FOCUS, CROPS

FIELDS = {
    'detail_edge': ('邻接边缘', ('让相邻元素停在画边', '保留主体边缘轮廓', '只露出一部分相邻色块', '沿板边预留窄缝')),
    'detail_layers': ('前后层次', ('背景只保留一小块场地线索', '相邻部件形成前后层次', '主体与后方留出清楚间隔', '压低背景对比突出局部')),
    'detail_space': ('局部留白', ('沿原有留白收边', '主体一侧多留少量空间', '四周紧凑但不切断识别点', '留出局部轮廓的呼吸空间')),
    'detail_focus': ('细节主体', FOCUS),
    'detail_surface': ('材质表现', ('保留真实明暗过渡', '呈现轮廓与底色的交界', '保留表面细微质感，不锐化造边', '保持参考色块之间的清晰区分')),
    'detail_art': ('原稿保留重点', ('保留可见图案原有线宽', '可见文字按原稿逐字呈现', '保留参考配色及相邻色块边界', '不拉伸局部图案或人物')),
    'detail_crop': ('局部构图', CROPS),
    'detail_light': ('细节受光', ('柔和侧光显出轮廓', '近正面柔光保留印刷色', '用现场漫射光保留暗部层次', '轻微侧向明暗差，不制造强反光')),
    'detail_plane': ('对焦层次', ('焦点落在主体可辨认的边缘', '让主要细节处于同一清晰范围', '背景稍软但能辨认场地', '保持自然景深，不用过度虚化')),
}
GROUPS = (('环境空间', ('environment',)), ('近景布置', ('detail_edge','detail_layers','detail_space')),
          ('近景内容', ('detail_focus','detail_surface','detail_art')),
          ('近景拍摄', ('detail_crop','camera','detail_light','detail_plane','ratio')))
LABELS = {**{k:v[0] for k,v in FIELDS.items()}, 'environment':'室内 / 室外','camera':'近景机位','ratio':'画面比例'}
DIMENSIONS = tuple((k,LABELS[k]) for _,keys in GROUPS for k in keys)

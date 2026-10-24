"""Shared photographic intent and permitted physical decorations."""
PHOTO_REQUIREMENTS = '''照片要求：生成一张普通人用手机后置主摄随手拍下的开业现场照片（candid smartphone photo），像未经精修的手机相册原片。
拍摄者站在正常可步行的位置，手机自然拿在胸口至眼睛高度，用后置主摄1倍拍摄；需要容纳完整装置时通过后退取景。不要贴地仰拍、抬高俯拍、航拍或超广角夸张透视。
天气只决定普通的现场天气和时段，不额外安排地面反光、戏剧性光影或特效。
使用现场自然光和店内现有灯光，曝光自然、颜色真实，保留阴影细节、地面使用痕迹和真实材质。手持取景略有自然偏差，景深符合手机主摄，不过度虚化；画面清楚，不故意模糊、做旧或添加明显噪点。
不要3D渲染、建筑效果图、棚拍布光、广告大片、电影调色、夸张HDR或发光轮廓。'''
DECORATION_REQUIREMENTS = '''装饰范围：现场开业装饰只使用KT板和气球；不添加花艺、鲜花、仿真花、干花、花束、花篮、开业花架、花环或花墙，也不把花材混入气球簇。即使参考现场有花艺，也移除实体花艺；KT板上原有的印刷图案仍按参考图保留。'''



def photo_requirements(camera='', camera_hidden=False, render_style=None):
    from scene_tool.config.render_styles import COMMERCIAL, COMMERCIAL_REQUIREMENTS
    if render_style == COMMERCIAL:
        text = COMMERCIAL_REQUIREMENTS
        if camera_hidden:
            text = text.replace('严格采用本轮指定的拍摄角度与等效焦距。选择75—150mm正面长焦时，相机对准装置中心、正面平视，成像平面与板面平行；通过足够的拍摄距离完整容纳装置，保持板材和人物原有比例、竖线端正，避免广角拉伸和近大远小的夸张透视。', '合理安排构图和拍摄距离，完整容纳装置，保持板材和人物原有比例，避免夸张透视。')
        return text
    text = PHOTO_REQUIREMENTS
    if camera_hidden or ('等效' in camera and 'mm' in camera):
        text = text.replace('后置主摄', '后置相机')
        text = text.replace('用后置相机1倍拍摄', '使用本轮指定的等效焦段拍摄' if not camera_hidden else '自然手持拍摄')
        text = text.replace('景深符合手机主摄', '景深符合实际焦段和拍摄距离')
    return text

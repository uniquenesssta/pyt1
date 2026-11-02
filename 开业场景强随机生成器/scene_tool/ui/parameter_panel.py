from scene_tool.config.defaults import DIMENSIONS, INDUSTRIES
from scene_tool.domain.industry_profiles import dimensions, industry_pools
from scene_tool.config.render_styles import COMMERCIAL
from scene_tool.ui.components.product_size import product_size_row
from scene_tool.ui.visibility_binding import change_opening
from scene_tool.ui.components.results import ResultList


def build_parameters(self, parent):
    self.parameter_host = parent
    for child in parent.winfo_children():
        child.destroy()
    results = ResultList(parent)
    self.combos, self.parameter_labels = {}, {}
    style = self.render_style.get()
    self.parameter_style = style
    labels = dict(dimensions(style))
    scoped = industry_pools(self.industry.get(), self.values['environment'].get(), style)
    results.group('产品规格（不参与随机）')
    if style == '近景摄影':
        results.result('拍摄对象', self.values['close_subject'], None)
        results.result('自定义材质', self.values['close_material'], None)
    else:
        product_size_row(results, self.product_size)
        results.result('开业类型', self.industry, None, choices=INDUSTRIES)
    from scene_tool.config.close_dimensions import GROUPS
    for title, fields in GROUPS if style == '近景摄影' else (
        ('环境空间', ('environment', 'architecture', 'display_space', 'background_depth') if style == COMMERCIAL else ('environment', 'architecture', 'city', 'address')),
        ('布置', ('placement', 'balloons')),
        ('板面内容', ('brand', 'logo_shape', 'logo_structure')),
        ('拍摄', ('detail_focus', 'detail_crop', 'camera', 'lighting', 'ratio') if style == '近景摄影' else ('camera', 'lighting', 'ratio')),
    ):
        results.group(title)
        for key in fields:
            self.parameter_labels[key] = results.result(
                labels[key], self.values[key], self.locks[key],
                choices=scoped.get(key, self.engine.pools.get(key, [])), readonly=key in ('environment', 'camera'),
                hidden=self.hidden[key], on_hide=lambda k=key: change_opening(self, k))
            self.combos[key] = self.parameter_labels[key].editor
            if style == '近景摄影' and key in ('detail_reflection', 'detail_light'):
                from scene_tool.ui.highlight_binding import bind_highlight
                bind_highlight(self, key)
            if style == '近景摄影' and key == 'camera':
                from scene_tool.ui.studio_binding import opening_camera_changed
                self.combos[key].bind('<<ComboboxSelected>>', lambda _: opening_camera_changed(self))
        if title == '板面内容':
            results.result('开业文案', self.copyline, self.copy_locked, hidden=self.hidden['copy'],
                           on_hide=lambda: change_opening(self, 'copy'))


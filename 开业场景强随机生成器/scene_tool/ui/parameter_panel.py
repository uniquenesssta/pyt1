from scene_tool.config.defaults import DIMENSIONS, INDUSTRIES
from scene_tool.ui.components.product_size import product_size_row
from scene_tool.ui.visibility_binding import change_opening
from scene_tool.ui.components.results import ResultList


def build_parameters(self, parent):
    results = ResultList(parent)
    self.combos, self.parameter_labels = {}, {}
    labels = dict(DIMENSIONS)
    results.group('产品规格（不参与随机）')
    product_size_row(results, self.product_size)
    results.result('开业类型', self.industry, None, choices=INDUSTRIES)
    for title, fields in (
        ('环境空间', ('environment', 'architecture', 'city', 'address')),
        ('布置', ('placement', 'balloons')),
        ('板面内容', ('brand', 'logo_shape', 'logo_structure')),
        ('拍摄', ('camera', 'lighting', 'ratio')),
    ):
        results.group(title)
        for key in fields:
            self.parameter_labels[key] = results.result(
                labels[key], self.values[key], self.locks[key],
                choices=self.engine.pools[key], readonly=key in ('environment', 'camera'),
                hidden=self.hidden[key], on_hide=lambda k=key: change_opening(self, k))
            self.combos[key] = self.parameter_labels[key].editor
        if title == '板面内容':
            results.result('开业文案', self.copyline, self.copy_locked, hidden=self.hidden['copy'],
                           on_hide=lambda: change_opening(self, 'copy'))


from scene_tool.config.defaults import DIMENSIONS
from scene_tool.ui.components.results import ResultList


def build_parameters(self, parent):
    results = ResultList(parent)
    self.combos, self.parameter_labels = {}, {}
    labels = dict(DIMENSIONS)
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
                choices=self.engine.pools[key], readonly=key == 'environment')
            self.combos[key] = self.parameter_labels[key].editor
        if title == '板面内容':
            results.result('开业文案', self.copyline, self.copy_locked)

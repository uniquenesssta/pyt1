"""选号页与结构页的双向跨区权重联动。"""
from ..core.cross_weights import cross_values, with_cross_values
from ..core.structure_profile import build_profile
from ..core.generation import MODES


class CrossWeightLink:
    def __init__(self, controls, page, error):
        self.controls, self.page, self.error = controls, page, error
        self.linked = False
        self.syncing = False
        controls.fill_button.configure(command=self.fill)
        page.on_change = self.from_profile
        for group in controls.weight_vars:
            for var in group:
                var.trace_add('write', self.from_entries)

    def fill(self):
        try:
            choice = self.controls.cross_period.get().strip()
            if choice == '跟随结构权重页':
                profile = self.page.snapshot()
            else:
                if choice == '全部':
                    periods = 0
                else:
                    try: periods = int(choice)
                    except ValueError as exc: raise ValueError('请输入正整数期数，或选择全部') from exc
                    if periods <= 0: raise ValueError('期数须大于0')
                profile = build_profile(self.page.draws, periods)
                # 完成计算再同步页面，失败不破坏已有配置。
                self.page.period.set(choice)
                self.page.profile = profile
                self.page.describe()
                self.page.render()
            self.linked = True
            self.controls.custom.set(True)
            self.controls.mode.set(MODES[2])
            self.controls.update_mode()
            self.controls.cross_period.set('跟随结构权重页')
            self.from_profile(profile)
        except ValueError as exc:
            self.error(exc)

    def from_profile(self, profile):
        if not self.linked: return
        self.syncing = True
        try:
            for variables, weights in zip(self.controls.weight_vars, cross_values(profile)):
                for var, weight in zip(variables, weights):
                    var.set(str(weight))
            self.describe(profile)
        finally:
            self.syncing = False

    def describe(self, profile):
        self.controls.cross_source.set(f'已联动：最近 {len(profile.draws)} 期 · 最大/起始跨区强度 {profile.strengths["最大跨区（差值>7）"]:g}/{profile.strengths["起始跨区"]:g}（0关闭）')

    def from_entries(self, *_):
        if self.syncing or not self.linked or self.page.profile is None: return
        try:
            values = [tuple(float(var.get()) for var in group) for group in self.controls.weight_vars]
            profile = with_cross_values(self.page.profile, values)
        except ValueError:
            self.controls.cross_source.set('跨区输入未完成或无效；修正后同步，生成时会校验')
            return
        self.page.profile = profile
        self.page.render()
        self.describe(profile)

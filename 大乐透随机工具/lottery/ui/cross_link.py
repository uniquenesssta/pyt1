"""选号页与结构页的双向跨区权重联动。"""
from math import isfinite
from ..core.cross_weights import CROSS_GROUPS, cross_values, with_cross_values
from ..core.structure_profile import build_profile


class CrossWeightLink:
    def __init__(self, controls, page, error):
        self.controls, self.page, self.error = controls, page, error
        # Both editors always represent the same profile once history is available.
        self.linked = True
        self.syncing = False
        controls.fill_button.configure(command=self.fill)
        page.on_change = self.from_profile
        for group in controls.weight_vars:
            for var in group:
                var.trace_add('write', self.from_entries)
        if page.profile is not None:
            self.from_profile(page.profile)

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
            self.controls.use_structure_mode()
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
        self.controls.cross_source.set(f'已联动：最近 {len(profile.draws)} 期 · 只有被选中的跨区指标才参与抽取')

    def _entry_weights(self, index):
        values = tuple(float(var.get()) for var in self.controls.weight_vars[index])
        if any(not isfinite(value) or not 0 <= value <= 100 for value in values):
            raise ValueError('跨区权重须为 0–100 的有限数值')
        return values

    def snapshot(self, selected):
        """只校验此次实际选用的跨区输入；其他草稿不阻塞抽取。"""
        profile = self.page.snapshot()
        if self.controls.custom.get():
            current = cross_values(profile)
            for index, name in enumerate(CROSS_GROUPS):
                if name not in selected:
                    continue
                try:
                    values = self._entry_weights(index)
                except ValueError:
                    values = ()
                if values != current[index]:
                    raise ValueError(f'{name}的跨区权重尚未同步，请修正输入或点“一键填入”')
        return profile

    def from_entries(self, *_):
        if self.syncing or not self.linked or self.page.profile is None: return
        profile = self.page.profile
        old = cross_values(profile)
        updated = list(old)
        incomplete = []
        for index, name in enumerate(CROSS_GROUPS):
            try:
                updated[index] = self._entry_weights(index)
            except ValueError:
                incomplete.append(name)
        if tuple(updated) != old:
            profile = with_cross_values(profile, updated)
            self.page.profile = profile
            self.page.render()
        if incomplete:
            self.controls.cross_source.set('输入未完成：' + '、'.join(incomplete) + '；只校验被选中的指标')
        else:
            self.describe(profile)

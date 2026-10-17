from scene_tool.config.paths import DATA, RESOURCES
from scene_tool.storage.json_files import load_json
from scene_tool.domain.prompt_migration import migrate_prompt_state
from scene_tool.storage.session import load_session, save_session

def save(self):
    state = {'copy_random': self.copy_random.get(), 'copy_locked': self.copy_locked.get(),
             'copy_recent': self.copy_engine.recent, 'values': self.current(), 'locks': {k: v.get() for k, v in self.locks.items()},
             'generated_names': self.generated_names.get(), 'recent': self.engine.recent,
             'strong': self.strong.get(), 'industry': self.industry.get(), 'copy': self.copyline.get(),
             'constraints': self.constraints.get('1.0', 'end-1c'), 'extra': self.extra.get('1.0', 'end-1c'),
             'prompt': self.prompt.get('1.0', 'end-1c'), 'rendered': self.rendered, 'bags': self.engine.bags}
    try:
        save_session(DATA / 'state.json', state)
        return True
    except OSError as exc:
        self.status.set(f'设置保存失败（仍可复制提示词）：{exc}')
        return False

def restore(self):
    path = DATA / 'state.json'
    if not path.exists():
        return
    try:
        legacy = tuple(load_json(RESOURCES / name)['constraints']
                       for name in ('legacy_prompt_v1.json', 'legacy_prompt_v2.json'))
        state = migrate_prompt_state(load_session(path), legacy)
        for key, value in state.get('values', {}).items():
            if key in self.values and isinstance(value, str):
                self.values[key].set(value)
        for key, value in state.get('locks', {}).items():
            if key in self.locks and isinstance(value, bool):
                self.locks[key].set(value)
        for name, variable in [('industry', self.industry), ('copy', self.copyline)]:
            if isinstance(state.get(name), str):
                variable.set(state[name])
        if isinstance(state.get('strong'), bool):
            self.strong.set(state['strong'])
        for name, widget in [('constraints', self.constraints), ('extra', self.extra), ('prompt', self.prompt)]:
            if isinstance(state.get(name), str):
                widget.delete('1.0', 'end')
                widget.insert('1.0', state[name])
        self.rendered = state.get('rendered', '') if isinstance(state.get('rendered', ''), str) else ''
        self.engine.restore_bags(state.get('bags'))
        self.engine.restore_recent(state.get('recent'))
        self.copy_engine.restore(state.get('copy_recent'))
        for name, variable in [('copy_random', self.copy_random), ('copy_locked', self.copy_locked)]:
            if isinstance(state.get(name), bool):
                variable.set(state[name])
        if isinstance(state.get('generated_names'), bool):
            self.generated_names.set(state['generated_names'])
        self.status.set('已恢复设置并升级未修改的默认提示词。自定义要求保留；可点“复原默认提示词”采用新版完整要求。')
    except (OSError, ValueError) as exc:
        self.startup_errors.append(f'上次设置无法读取，已尽可能恢复有效内容。\n{exc}')

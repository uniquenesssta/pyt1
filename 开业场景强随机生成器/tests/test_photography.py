import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scene_tool.config.paths import RESOURCES
from scene_tool.config.defaults import DEFAULT_CONSTRAINTS
from scene_tool.config.photography import PHOTO_REQUIREMENTS, DECORATION_REQUIREMENTS
from scene_tool.domain.prompts import make_prompt
from scene_tool.domain.prompt_migration import migrate_prompt_state
from scene_tool.storage.json_files import load_json
from scene_tool.storage.pools import load_pools
from scene_tool.generation.parameters import Randomizer


class PhotoTests(unittest.TestCase):
    def setUp(self):
        self.values = Randomizer(load_pools(RESOURCES / 'pools.json')).draw()
        self.legacy = load_json(RESOURCES / 'legacy_prompt_v1.json')['constraints']

    def test_photo_and_no_flowers_including_with_custom_constraints(self):
        # This assertion covers the 1x template; telephoto has separate coverage.
        self.values['camera'] = '正面平视，手持手机后置主摄1倍拍摄'
        prompt = make_prompt(self.values, constraints='保持我的红色背景')
        self.assertIn(PHOTO_REQUIREMENTS, prompt)
        self.assertIn(DECORATION_REQUIREMENTS, prompt)
        self.assertIn('保持我的红色背景', prompt)
        self.assertNotIn('摄影效果图', prompt)

    def test_migrate_defaults_and_cached_generated_prompt(self):
        state = {'values': self.values, 'constraints': self.legacy, 'prompt': '旧提示词', 'rendered': '旧提示词'}
        new = migrate_prompt_state(state, self.legacy)
        self.assertEqual(new['constraints'], DEFAULT_CONSTRAINTS)
        self.assertIn(DECORATION_REQUIREMENTS, new['prompt'])
        self.assertEqual(new['prompt'], new['rendered'])
        self.assertEqual(state['constraints'], self.legacy)

    def test_keep_manual_edits_and_custom_background(self):
        state = {'values': self.values, 'constraints': '保留红色背景', 'prompt': '我改过的内容', 'rendered': '旧输出'}
        self.assertEqual(migrate_prompt_state(state, self.legacy), state)

    def test_idempotent_migration(self):
        state = {'values': self.values, 'constraints': self.legacy, 'prompt': '旧', 'rendered': '旧'}
        new = migrate_prompt_state(state, self.legacy)
        self.assertEqual(migrate_prompt_state(new, self.legacy), new)

    def test_both_default_versions_upgrade_without_losing_other_state(self):
        previous = load_json(RESOURCES / 'legacy_prompt_v2.json')['constraints']
        versions = (self.legacy, previous)
        for old in versions:
            state = {'values': self.values, 'constraints': old, 'prompt': '手改提示词',
                     'rendered': '旧输出', 'extra': '不要行人', 'locks': {'brand': True}}
            new = migrate_prompt_state(state, versions)
            self.assertEqual(new, dict(state, constraints=DEFAULT_CONSTRAINTS))
        custom = dict(state, constraints=previous + '\n我的新要求')
        self.assertEqual(migrate_prompt_state(custom, versions), custom)


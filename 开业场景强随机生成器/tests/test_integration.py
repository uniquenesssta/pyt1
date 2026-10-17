"""Regression checks for package boundaries, saved data and editor callbacks."""
import importlib
import json
from pathlib import Path
import pkgutil
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import scene_tool
from scene_tool.config.paths import BASE, DATA, RESOURCES
from scene_tool.storage.pools import load_startup_pools, load_pools
from scene_tool.storage.session import load_session, save_session
from scene_tool.ui.prompt_controller import PromptController
from scene_tool.generation.parameters import Randomizer
from scene_tool.domain.prompts import make_prompt


class IntegrationTests(unittest.TestCase):
    def test_all_modules_import_without_opening_a_window(self):
        for item in pkgutil.walk_packages(scene_tool.__path__, 'scene_tool.'):
            importlib.import_module(item.name)
        importlib.import_module('app')

    def test_resource_and_user_data_paths(self):
        self.assertEqual(DATA, BASE / 'data')
        self.assertTrue((RESOURCES / 'pools.json').is_file())
        self.assertTrue((BASE / '启动.bat').is_file())

    def test_legacy_state_roundtrip_preserves_edits_and_history(self):
        state = {'values': {'brand': 'LUMINA 露米娜'}, 'locks': {'brand': True},
                 'prompt': '手动编辑后的提示词', 'rendered': '旧模板',
                 'constraints': '用户自定义背景', 'copy_random': False,
                 'recent': {'brand': ['LUMINA 露米娜']}, 'copy_recent': ['主句 ｜ 副句']}
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'state.json'
            save_session(path, state)
            self.assertEqual(load_session(path), state)
            path.write_text('[]')
            with self.assertRaises(ValueError):
                load_session(path)

    def test_custom_pool_fallback_and_upgrade(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'custom_pools.json'
            path.write_text('{bad json')
            pools, errors = load_startup_pools(path)
            self.assertEqual(len(errors), 1)
            legacy = json.loads((RESOURCES / 'legacy_pools_v1.json').read_text())
            pools.update(legacy)
            pools['brand'] = ['自选品牌1', '自选品牌2']
            path.write_text(json.dumps(pools))
            pools, errors = load_startup_pools(path)
            self.assertFalse(errors)
            self.assertEqual(len(pools['city']), 159)
            self.assertEqual(pools['brand'], ['自选品牌1', '自选品牌2'])
            # Startup reads must not overwrite the user's stored custom file.
            self.assertEqual(json.loads(path.read_text())['city'], legacy['city'])

    def test_package_generates_complete_prompt(self):
        engine = Randomizer(load_pools(RESOURCES / 'pools.json'))
        self.assertIn('品牌名称：', make_prompt(engine.draw()))

    def test_export_dialog_uses_window_and_preserves_current_text(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'prompt.txt'
            view = SimpleNamespace(pending=None,
                prompt=SimpleNamespace(get=lambda *_: '当前手改文字'),
                status=SimpleNamespace(set=lambda _: None))
            with patch('scene_tool.ui.prompt_controller.filedialog.asksaveasfilename', return_value=str(path)) as ask:
                PromptController(view).export()
            self.assertIs(ask.call_args.kwargs['parent'], view)
            self.assertEqual(path.read_text(encoding='utf-8-sig'), '当前手改文字')

    def test_parameter_change_does_not_overwrite_manual_prompt(self):
        messages = []
        view = SimpleNamespace(pending=None, rendered='原始提示词',
            prompt=SimpleNamespace(get=lambda *_: '手动修改'),
            status=SimpleNamespace(set=messages.append))
        self.assertFalse(PromptController(view).refresh())
        self.assertIn('已保留', messages[0])

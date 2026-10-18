"""Migration and compact persistence must retain user work and random progress."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scene_tool.domain.scene_model import SceneModel
from scene_tool.storage.scenes import load_profiles
from scene_tool.storage.scene_sessions import load_states, save_states
from scene_tool.storage.json_files import atomic_json, load_json
from scene_tool.storage.scene_codec import encode_scene, decode_scene
from scene_tool.ui.components.compact_text import fit_text


class SceneStorageTests(unittest.TestCase):
    def setUp(self):
        self.profiles = load_profiles()
        self.models = {p['name']: SceneModel(p) for p in self.profiles}

    def test_compact_roundtrip_including_custom_pool_and_manual_prompt(self):
        for model in self.models.values():
            model.set_pool('camera', ['自定左侧', '自定右侧'])
            model.draw()
            model.locks['camera'] = True
            model.extra = '额外要求'
            model.prompt = '手改文字'
            restored = SceneModel(model.profile, decode_scene(model.profile, encode_scene(model)))
            self.assertEqual(restored.state(), model.state())

    def test_migrate_combined_file_and_keep_other_scenes_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original = {'active': '酒店大厅', 'scenes': {k: m.state() for k, m in self.models.items()}}
            atomic_json(root / 'scene_modes.json', original)
            self.assertEqual(load_states(root, self.profiles)['scenes'], original['scenes'])
            save_states(root, original['active'], self.models)
            self.assertNotIn('scenes', load_json(root / 'scene_modes.json'))
            restored = load_states(root, self.profiles)
            for profile in self.profiles:
                self.assertEqual(SceneModel(profile, restored['scenes'][profile['name']]).state(), self.models[profile['name']].state())
            paths = list((root / 'scenes').glob('*.json'))
            times = {p: p.stat().st_mtime_ns for p in paths}
            self.models['酒店大厅'].draw()
            save_states(root, '酒店大厅', self.models)
            for path in paths:
                if path.stem != 'hotel_lobby':
                    self.assertEqual(path.stat().st_mtime_ns, times[path])

    def test_failed_migration_does_not_replace_legacy_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original = {'active': '酒店大厅', 'scenes': {k: m.state() for k, m in self.models.items()}}
            atomic_json(root / 'scene_modes.json', original)
            with patch('scene_tool.storage.scene_sessions.atomic_json', side_effect=OSError('磁盘错误')):
                with self.assertRaises(OSError):
                    save_states(root, '酒店大厅', self.models)
            self.assertEqual(load_json(root / 'scene_modes.json'), original)

    def test_updated_default_pool_discards_old_indices(self):
        model = self.models['酒店大厅']
        encoded = encode_scene(model)
        profile = json.loads(json.dumps(model.profile))
        profile['dimensions'][0]['options'].reverse()
        decoded = decode_scene(profile, encoded)
        self.assertEqual(decoded['bags'][profile['dimensions'][0]['key']], [])

    def test_broken_scene_does_not_block_other_scenes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            save_states(root, '酒店大厅', self.models)
            (root / 'scenes/hotel_lobby.json').write_text('{broken')
            loaded = load_states(root, self.profiles)
            self.assertEqual(len(loaded['errors']), 1)
            self.assertEqual(len(loaded['scenes']), 6)

    def test_compact_preview_fits_and_marks_truncation(self):
        self.assertEqual(fit_text('abcdefg', 3, 2, len), 'abc\nde…')
        self.assertEqual(fit_text('abc', 3, 2, len), 'abc')
        self.assertEqual(fit_text('第一行\n第二行', 4, 1, len), '第一行…')


if __name__ == '__main__':
    unittest.main()

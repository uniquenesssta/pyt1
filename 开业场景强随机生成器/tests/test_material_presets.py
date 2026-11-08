import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from scene_tool.config.closeup import CLOSEUP
from scene_tool.storage import material_presets as storage
from scene_tool.storage.scenes import load_profiles
from scene_tool.domain.scene_model import SceneModel
from scene_tool.ui.material_binding import apply_material
from test_variant_binding import opening_view, Value


class MaterialPresetTests(unittest.TestCase):
    def test_save_load_update_and_delete_unicode_without_changing_other_presets(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'material_presets.json'
            self.assertEqual(storage.load(path),{})
            storage.save('细面写真布','正面细腻，无粗织网格',path)
            storage.save('红纸','细腻微光红纸，保持原色',path)
            storage.save('细面写真布','只见微细表面纹理',path)
            self.assertEqual(storage.load(path)['细面写真布'],'只见微细表面纹理')
            storage.delete('细面写真布',path)
            self.assertEqual(storage.load(path),{'红纸':'细腻微光红纸，保持原色'})
            with self.assertRaises(ValueError): storage.save('空',' ',path)

    def test_corrupt_file_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'material_presets.json'
            for invalid in ('{broken','[]','{"x":3}'):
                path.write_text(invalid)
                with self.assertRaises(ValueError): storage.save('红纸','红纸外观',path)
                with self.assertRaises(ValueError): storage.delete('红纸',path)
                self.assertEqual(path.read_text(),invalid)

    def test_opening_apply_updates_prompt_and_disk_without_changing_light(self):
        view=opening_view(CLOSEUP)
        before=view.current()
        with tempfile.TemporaryDirectory() as folder, patch('scene_tool.ui.session_binding.DATA',Path(folder)):
            self.assertTrue(apply_material(view,'细面涂层，按材质实拍保留底色'))
            state=json.loads((Path(folder)/'state.json').read_text())
        self.assertIn('细面涂层，按材质实拍保留底色',view.prompt.get())
        self.assertEqual(view.prompt.get(),view.generated())
        self.assertEqual(state['prompt'],view.prompt.get())
        for key in ('camera','detail_reflection','detail_light','close_subject'):
            self.assertEqual(view.values[key].get(),before[key])

    def test_decline_manual_replacement_does_not_apply_material(self):
        view=opening_view(CLOSEUP)
        view.prompt.set('手改文字')
        before=view.current()
        with patch('scene_tool.ui.material_binding.messagebox.askyesno',return_value=False):
            self.assertFalse(apply_material(view,'其他材质'))
        self.assertEqual(view.current(),before)
        self.assertEqual(view.prompt.get(),'手改文字')

    def test_all_scene_materials_flow_to_model_prompt_and_save(self):
        for profile in load_profiles():
            model=SceneModel(profile,{'render_style':CLOSEUP})
            panel=SimpleNamespace(model=model,close_material=Value(''),updating=False,
                allow_replace=Mock(return_value=True),show_prompt=Mock(),persist=Mock())
            def capture(): model.close_material=panel.close_material.get()
            panel.capture=capture
            self.assertTrue(apply_material(panel,'我的实物表面描述',scene=True))
            self.assertIn('我的实物表面描述',model.prompt)
            self.assertEqual(model.generate(),model.prompt)
            self.assertEqual(SceneModel(profile,model.state()).close_material,'我的实物表面描述')
            panel.persist.assert_called_once()


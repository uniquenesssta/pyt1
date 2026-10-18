import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scene_tool.config.paths import RESOURCES
from scene_tool.storage.pools import load_pools
from scene_tool.generation.parameters import Randomizer
from scene_tool.domain.pools import validate_pools
from scene_tool.domain.environment import scene_parameters
from scene_tool.domain.prompt_migration import migrate_prompt_state
from scene_tool.domain.prompts import make_prompt


class EnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.pools = load_pools(RESOURCES / 'pools.json')

    def test_old_custom_pool_retains_custom_values(self):
        del self.pools['environment']
        self.pools['camera'] = ['我的视角一', '我的视角二']
        result = validate_pools(self.pools)
        self.assertEqual(result['environment'], ['室内', '室外'])
        self.assertEqual(result['camera'], self.pools['camera'])

    def test_old_session_preserves_parameters_and_manual_text(self):
        values = Randomizer(self.pools).draw()
        del values['environment']
        state = {'values': values, 'prompt': '手改', 'rendered': '旧内容'}
        result = migrate_prompt_state(state, ())
        self.assertEqual(result['values'], dict(values, environment='室外'))
        self.assertEqual(result['prompt'], '手改')
        self.assertNotIn('environment', values)

    def test_indoor_camera_and_placement_are_resolved(self):
        values = Randomizer(self.pools).draw()
        values.update(environment='室内', camera='站在街道对面的人行道上，手持手机拍向店面', placement='门前空地偏左斜放')
        resolved = scene_parameters(values)
        self.assertNotIn('人行道', resolved['camera'])
        self.assertEqual(resolved['placement'], '室内入口旁空地偏左斜放')
        self.assertIn('室内不出现车辆', make_prompt(values))
        self.assertEqual(values['placement'], '门前空地偏左斜放')

    def test_environment_lock_and_switch(self):
        engine = Randomizer(self.pools)
        values = engine.draw()
        locked = engine.draw(values, ['environment'])
        self.assertEqual(locked['environment'], values['environment'])
        self.assertNotEqual(engine.draw(values)['environment'], values['environment'])

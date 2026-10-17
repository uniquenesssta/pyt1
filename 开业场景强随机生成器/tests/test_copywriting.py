import random
import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scene_tool.config.copy_phrases import HEADLINES, SUBLINES, SEPARATOR
from scene_tool.generation.copywriting import CopyRandomizer


class CopyTests(unittest.TestCase):
    def test_200_unique_complete_phrases(self):
        self.assertEqual(len(HEADLINES), 100)
        self.assertEqual(len(SUBLINES), 100)
        self.assertEqual(len(set(HEADLINES + SUBLINES)), 200)
        self.assertTrue(all(s.strip() and SEPARATOR not in s for s in HEADLINES + SUBLINES))

    def test_cross_pairing_and_recent_repeat_avoidance(self):
        engine = CopyRandomizer(random.Random(333))
        current = ''
        history = []
        for _ in range(250):
            value = engine.draw(current)
            head, sub = value.split(SEPARATOR)
            self.assertIn(head, HEADLINES)
            self.assertIn(sub, SUBLINES)
            self.assertNotIn(value, history[-200:])
            if current:
                old_head, old_sub = current.split(SEPARATOR)
                self.assertNotEqual(head, old_head)
                self.assertNotEqual(sub, old_sub)
            history.append(value)
            current = value
        self.assertEqual(engine.recent, history[-200:])

    def test_disabled_or_locked_preserves_manual_copy_and_history(self):
        engine = CopyRandomizer()
        for enabled, locked in [(False, False), (True, True), (False, True)]:
            self.assertEqual(engine.draw('自填文案', enabled, locked), '自填文案')
        self.assertEqual(engine.recent, [])

    def test_restore_and_resume(self):
        engine = CopyRandomizer(random.Random(8))
        current = engine.draw()
        resumed = CopyRandomizer(random.Random(8))
        resumed.restore(engine.recent)
        self.assertNotEqual(resumed.draw(), current)
        resumed.restore([None, {}, '保留文字'])
        self.assertEqual(resumed.recent, ['保留文字'])

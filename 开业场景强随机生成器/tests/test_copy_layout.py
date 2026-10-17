"""Generated pairs get roles; custom punctuation and text remain intact."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scene_tool.domain.copy_layout import copy_instructions


class CopyLayoutTests(unittest.TestCase):
    def test_generated_pair_assigns_two_distinct_roles(self):
        lines = copy_instructions('你好，新朋友 ｜ 以热爱装点此间日常')
        self.assertEqual(json.loads(lines[0].split('：', 1)[1]), '你好，新朋友')
        self.assertEqual(json.loads(lines[1].split('：', 1)[1]), '以热爱装点此间日常')

    def test_custom_copy_roundtrips_without_guessing_separators(self):
        for text in ('盛大开业 · 美好启幕', 'A|B', 'A ｜ B ｜ C', '欢迎“你”\n明天见'):
            lines = copy_instructions(text)
            self.assertEqual(len(lines), 1)
            self.assertEqual(json.loads(lines[0].split('：', 1)[1]), text)

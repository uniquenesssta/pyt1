"""启动失败必须可见，并返回失败状态。"""
import unittest
from unittest.mock import patch

from liuyao_tool.startup.runner import run


class StartupTests(unittest.TestCase):
    def test_failed_initialization_is_reported(self):
        with patch("liuyao_tool.application.main", side_effect=RuntimeError("startup failure")), \
                patch("liuyao_tool.startup.runner.show_exception") as report:
            self.assertEqual(run(), 1)
        report.assert_called_once()
        self.assertIs(report.call_args.args[0], RuntimeError)
        self.assertEqual(str(report.call_args.args[1]), "startup failure")

    def test_success_returns_zero(self):
        with patch("liuyao_tool.application.main") as main, \
                patch("liuyao_tool.startup.runner.show_exception") as report:
            self.assertEqual(run(), 0)
        main.assert_called_once_with()
        report.assert_not_called()


if __name__ == "__main__":
    unittest.main()

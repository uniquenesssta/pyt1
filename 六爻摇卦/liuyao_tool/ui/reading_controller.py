"""协调同一组卦象的解读、问题修改与剪贴板操作。"""
from ..interpretation.engine import analyze
from ..interpretation.formatting import format_reading, format_references


class ReadingController:
    def __init__(self, root, panel, catalog):
        self.root = root
        self.panel = panel
        self.catalog = catalog
        self._hexagram = None
        self._copy_text = ""
        panel.bind_actions(self.generate, self.copy, self.context_changed)
        self.reset()

    def reset(self):
        self._hexagram = None
        self._copy_text = ""
        self.panel.clear()

    def set_result(self, hexagram):
        self._hexagram = hexagram
        self.generate()

    def generate(self):
        if self._hexagram is None:
            return
        question, background = self.panel.get_context()
        report = analyze(self._hexagram, self.catalog, question, background)
        self._copy_text = format_reading(report)
        self.panel.show_report(self._copy_text, format_references(report))

    def context_changed(self):
        self._copy_text = ""
        if self._hexagram is not None:
            self.panel.show_stale()

    def copy(self):
        if not self._copy_text:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(self._copy_text)
        self.panel.show_copied()

"""Carry the current scrollbar position across scene switches."""


class PromptScrollMemory:
    def __init__(self, scheduler):
        self.scheduler = scheduler
        self.position = 0.0
        self.pending = None

    def remember(self, widget):
        # A rapid second switch must retain the position still awaiting apply.
        if self.pending is None:
            first, last = widget.yview()
            travel = 1.0 - (last - first)
            if travel > 1e-9:
                self.position = min(1.0, max(0.0, first / travel))
        self.cancel()

    def cancel(self):
        if self.pending is not None:
            self.scheduler.after_cancel(self.pending)
        self.pending = None

    def restore(self, widget):
        self.cancel()
        def apply():
            self.pending = None
            if widget.winfo_exists() and widget.winfo_ismapped():
                first, last = widget.yview()
                travel = max(0.0, 1.0 - (last - first))
                widget.yview_moveto(self.position * travel)
        self.pending = self.scheduler.after_idle(apply)

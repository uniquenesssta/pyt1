"""Carry one shared scrollbar position across every scene, after layout."""


class PromptScrollMemory:
    def __init__(self, scheduler):
        self.scheduler = scheduler
        self.position = 0.0
        self.pending = None

    def remember(self, widget):
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
            # A newly shown Text can still report the hidden panel's dimensions
            # during the first idle callback. Flush geometry and wrapping first.
            if not widget.winfo_exists():
                self.pending = None
                return
            widget.update_idletasks()
            if not widget.winfo_ismapped():
                self.pending = None
                return
            # Ask Text for its actual bottom limit rather than estimating it
            # from the visible fraction of a previously hidden viewport.
            widget.yview_moveto(1.0)
            bottom = widget.yview()[0]
            widget.yview_moveto(self.position * bottom)
            self.pending = None

        def settled():
            # Run after map/geometry idle handlers, on the next event-loop turn.
            self.pending = self.scheduler.after(1, apply)

        self.pending = self.scheduler.after_idle(settled)

"""Defer expensive Text wrapping until a resize burst has settled."""


class ResizeController:
    def __init__(self, window, widgets, delay=180):
        self.window = window
        self.widgets = widgets
        self.delay = delay
        self.size = None
        self.pending = None
        self.snapshot = None
        window.bind('<Configure>', self.on_configure, add='+')
        window.bind('<Destroy>', self.on_destroy, add='+')

    def on_configure(self, event):
        if event.widget is not self.window:
            return
        size = (event.width, event.height)
        if self.size is None:
            self.size = size
            return
        if size == self.size:
            return  # Moving the title bar does not reflow the text.
        self.size = size
        if self.pending is not None:
            self.window.after_cancel(self.pending)
        if self.snapshot is None:
            self.snapshot = [(widget, widget.cget('wrap'), widget.index('@0,0'))
                             for widget in self.widgets]
            for widget, _, _ in self.snapshot:
                widget.configure(wrap='none')
        self.pending = self.window.after(self.delay, self.restore)

    def restore(self):
        self.pending = None
        snapshot, self.snapshot = self.snapshot, None
        for widget, wrap, top in snapshot or ():
            widget.configure(wrap=wrap)
            widget.xview_moveto(0)
            widget.yview(top)

    def on_destroy(self, event):
        if event.widget is self.window and self.pending is not None:
            self.window.after_cancel(self.pending)
            self.pending = None
            self.snapshot = None

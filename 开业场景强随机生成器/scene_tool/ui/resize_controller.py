"""Suspend wrapping for the entire native border-drag operation."""
from scene_tool.ui.windows_resize import WindowsResizeHook


class ResizeController:
    def __init__(self, window, widgets):
        self.window = window
        self.widgets = widgets
        self.snapshot = None
        self.hook = WindowsResizeHook(window, self.pause, self.restore)
        self.install_pending = window.after_idle(self.install)
        window.bind('<Destroy>', self.on_destroy, add='+')

    def install(self):
        self.install_pending = None
        self.hook.install()

    def pause(self):
        if self.snapshot is not None:
            return
        self.snapshot = [(widget, widget.cget('wrap'), widget.index('@0,0'))
                         for widget in self.widgets]
        for widget, _, _ in self.snapshot:
            widget.configure(wrap='none')

    def restore(self):
        snapshot, self.snapshot = self.snapshot, None
        for widget, wrap, top in snapshot or ():
            widget.configure(wrap=wrap)
            widget.xview_moveto(0)
            widget.yview(top)

    def on_destroy(self, event):
        if event.widget is not self.window:
            return
        if self.install_pending is not None:
            self.window.after_cancel(self.install_pending)
            self.install_pending = None
        self.hook.close()
        self.snapshot = None

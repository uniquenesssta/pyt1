"""Freeze the whole client layout while the user holds a resize border."""
from scene_tool.ui.windows_resize import primary_button_down


class ResizeController:
    def __init__(self, window, surface, button_down=primary_button_down):
        self.window, self.surface = window, surface
        self.button_down = button_down
        self.height_offset = 0
        self.size = None
        self.frozen = False
        self.pending = None
        window.bind('<Configure>', self.on_configure, add='+')
        window.bind('<Destroy>', self.on_destroy, add='+')

    def on_configure(self, event):
        if event.widget is not self.window:
            return
        size = (event.width, event.height)
        previous = self.size
        self.size = size
        if previous is None or previous == size or self.frozen:
            return
        if self.button_down():
            self.frozen = True
            self.surface.place_configure(relwidth=0, relheight=0,
                                         width=previous[0], height=previous[1] + self.height_offset)
            self.pending = self.window.after(20, self.check_release)

    def check_release(self):
        self.pending = None
        if self.button_down():
            self.pending = self.window.after(20, self.check_release)
            return
        self.frozen = False
        self.surface.place_configure(width=0, height=self.height_offset, relwidth=1, relheight=1)

    def on_destroy(self, event):
        if event.widget is self.window and self.pending is not None:
            self.window.after_cancel(self.pending)
            self.pending = None

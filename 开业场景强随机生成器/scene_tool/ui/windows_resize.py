"""Observe the native Windows sizing loop, including pauses while holding the mouse."""
import ctypes
import sys
from ctypes import wintypes


class WindowsResizeHook:
    def __init__(self, window, begin, end):
        self.window, self.begin, self.end = window, begin, end
        self.hwnd = None
        self.callback = None
        self.previous = None

    def install(self):
        if sys.platform != 'win32' or self.hwnd is not None:
            return
        user = ctypes.WinDLL('user32', use_last_error=True)
        pointer = ctypes.c_ssize_t
        proc_type = ctypes.WINFUNCTYPE(pointer, wintypes.HWND, wintypes.UINT,
                                      wintypes.WPARAM, wintypes.LPARAM)
        user.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
        user.GetAncestor.restype = wintypes.HWND
        self.set_proc = user.SetWindowLongPtrW if ctypes.sizeof(ctypes.c_void_p) == 8 else user.SetWindowLongW
        self.set_proc.argtypes = [wintypes.HWND, ctypes.c_int, pointer]
        self.set_proc.restype = pointer
        user.CallWindowProcW.argtypes = [ctypes.c_void_p, wintypes.HWND, wintypes.UINT,
                                        wintypes.WPARAM, wintypes.LPARAM]
        user.CallWindowProcW.restype = pointer
        self.user = user
        hwnd = user.GetAncestor(self.window.winfo_id(), 2)  # GA_ROOT: Tk's outer frame

        def dispatch(handle, message, wparam, lparam):
            try:
                if message == 0x0214:  # WM_SIZING: actual border resize, not title-bar movement
                    self.begin()
                elif message == 0x0232:  # WM_EXITSIZEMOVE: mouse released / resize cancelled
                    self.end()
            except Exception:
                self.window.report_callback_exception(*sys.exc_info())
            return user.CallWindowProcW(self.previous, handle, message, wparam, lparam)

        self.callback = proc_type(dispatch)  # Keep alive while installed.
        ctypes.set_last_error(0)
        previous = self.set_proc(hwnd, -4, ctypes.cast(self.callback, ctypes.c_void_p).value)
        if not previous and ctypes.get_last_error():
            raise ctypes.WinError(ctypes.get_last_error())
        self.previous, self.hwnd = previous, hwnd

    def close(self):
        if self.hwnd is not None:
            self.set_proc(self.hwnd, -4, self.previous)
            self.hwnd = None

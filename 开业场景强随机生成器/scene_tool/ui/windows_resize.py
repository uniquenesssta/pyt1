"""Read the physical primary mouse button, including non-client window borders."""
import ctypes
import sys


def primary_button_down():
    if sys.platform != 'win32':
        return False
    user = ctypes.windll.user32
    # Respect swapped mouse buttons (SM_SWAPBUTTON).
    key = 0x02 if user.GetSystemMetrics(23) else 0x01
    return bool(user.GetAsyncKeyState(key) & 0x8000)

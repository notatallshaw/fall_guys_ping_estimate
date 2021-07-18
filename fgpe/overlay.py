# Standard Library
import tkinter as tk
from typing import Callable

# Third Party Libraries
import win32api
import win32con
import pywintypes


class Overlay:
    def __init__(self,
                 get_new_text_callback: Callable[[], str],
                 update_frequency_ms: int = 5_000):
        self.get_new_text_callback = get_new_text_callback
        self.update_frequency_ms = update_frequency_ms
        self.root = tk.Tk()
        self.ping_text = tk.StringVar()
        self.label = tk.Label(
            self.root,
            textvariable=self.ping_text,
            font=('Consolas', '16'),
            fg='green',
            bg='black'
        )
        self.label.master.overrideredirect(True)
        self.label.master.geometry("+10+10")
        self.label.master.lift()
        self.label.master.wm_attributes("-topmost", True)
        self.label.master.wm_attributes("-disabled", True)
        self.label.master.wm_attributes("-transparentcolor", "white")

        hWindow = pywintypes.HANDLE(int(self.label.master.frame(), 16))

        # http://msdn.microsoft.com/en-us/library/windows/desktop/ff700543(v=vs.85).aspx
        # The WS_EX_TRANSPARENT flag makes events (like mouse clicks) fall through the window.
        exStyle = win32con.WS_EX_COMPOSITED | win32con.WS_EX_LAYERED | win32con.WS_EX_NOACTIVATE | win32con.WS_EX_TOPMOST | win32con.WS_EX_TRANSPARENT
        win32api.SetWindowLong(hWindow, win32con.GWL_EXSTYLE, exStyle)

    def grid(self):
        self.label.pack()

    def update_label(self):
        self.ping_text.set(self.get_new_text_callback())
        self.root.after(self.update_frequency_ms, self.update_label)

    def run(self):
        self.grid()
        self.root.after(0, self.update_label)
        self.root.mainloop()


if __name__ == '__main__':
    import random
    overlay = Overlay(lambda: str(random.choice([1, 2, 3])))
    overlay.run()
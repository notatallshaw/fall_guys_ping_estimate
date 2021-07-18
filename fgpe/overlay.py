# Standard Library
import sys
import tkinter as tk
from typing import Callable


class Overlay:
    def __init__(self,
                 get_new_text_callback: Callable[[], str],
                 update_frequency_ms: int = 5_000):
        self.get_new_text_callback = get_new_text_callback
        self.update_frequency_ms = update_frequency_ms
        self.root = tk.Tk()

        # Set Closed Label
        self.close_label = tk.Label(
            self.root,
            text=' X |',
            font=('Consolas', '14'),
            fg='green',
            bg='black'
        )
        self.close_label.bind("<Button-1>", lambda _: sys.exit())
        self.close_label.grid(row=0, column=0)

        # Set up Ping Label
        self.ping_text = tk.StringVar()
        self.ping_label = tk.Label(
            self.root,
            textvariable=self.ping_text,
            font=('Consolas', '14'),
            fg='green',
            bg='black'
        )
        self.ping_label.grid(row=0, column=1)

        # Set Window Geometery
        self.root.overrideredirect(True)
        self.root.geometry("+10+10")
        self.root.lift()
        self.root.wm_attributes("-topmost", True)

    def update_label(self):
        self.ping_text.set(self.get_new_text_callback())
        self.root.after(self.update_frequency_ms, self.update_label)

    def run(self):
        self.root.after(0, self.update_label)
        self.root.mainloop()

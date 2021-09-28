# Standard Library
import tkinter as tk
from typing import Callable, Any


class Overlay:
    """
    Creates an overlay window using tkinter
    Uses the "-topmost" property to always stay on top of other Windows
    """
    def __init__(self,
                 close_callback: Callable[[Any], None],
                 initial_text: str,
                 initial_delay: int,
                 get_new_text_callback: Callable[[], tuple[int, str]]):
        self.close_callback = close_callback
        self.initial_text = initial_text
        self.initial_delay = initial_delay
        self.get_new_text_callback = get_new_text_callback
        self.root = tk.Tk()

        # Set up Close Label
        self.close_label = tk.Label(
            self.root,
            text=' X |',
            font=('Consolas', '14'),
            fg='green3',
            bg='grey19'
        )
        self.close_label.bind("<Button-1>", close_callback)
        self.close_label.grid(row=0, column=0)

        # Set up Ping Label
        self.ping_text = tk.StringVar()
        self.ping_label = tk.Label(
            self.root,
            textvariable=self.ping_text,
            font=('Consolas', '14'),
            fg='green3',
            bg='grey19'
        )
        self.ping_label.grid(row=0, column=1)

        # Define Window Geometery
        self.root.overrideredirect(True)
        self.root.geometry("+5+5")
        self.root.lift()
        self.root.wm_attributes("-topmost", True)

    def update_label(self) -> None:
        wait_time, update_text = self.get_new_text_callback()
        self.ping_text.set(update_text)
        self.root.after(wait_time, self.update_label)

    def run(self) -> None:
        self.ping_text.set(self.initial_text)
        self.root.after(self.initial_delay, self.update_label)
        self.root.mainloop()

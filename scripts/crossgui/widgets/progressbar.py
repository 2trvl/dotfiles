'''
This file is part of 2trvl/crossgui
Common widgets between different environments
Which is released under BSD-2-Clause license
Copyright (c) 2023 Andrew Shteren
---------------------------------------------
                 Progressbar                 
---------------------------------------------
Run a simplified progress bar for an unknown
process time or use common

'''
import multiprocessing
import threading
import time

from ..runtime.terminal import (
    change_cursor_visibility,
    clear_screen
)


class ProgressBar():
    def __init__(
        self,
        size: int = 30,
        unit: str = "",
        prefix: str = "",
        frames: str = "-\|/=",
        timeout: float = 0.1,
        clearMode: bool = False
    ):
        '''
        Progress bar for unknown process time

        Args:
            size (int, optional): Bar length. Defaults to 30.
            unit (str, optional): Task unit. With a negative
                counter can be used as a postfix. Defaults to "".
            prefix (str, optional): Prefix. Defaults to "".
            frames (str, optional): Animation. Last character
                for finished state. Defaults to "-\|/=".
            timeout (float, optional): Pause between renders
                used in start_rendering(). Defaults to 0.1.
            clearMode (bool, optional): Redraws each frame of
                the progress bar, clearing the previous one.
                It makes sense to activate this option if you
                are changing the prefix, unit, or even the size.
                Otherwise, characters of previous frame will remain
                in the terminal if it was longer. Defaults to False.

        Modify the following special variables to control
        progress bar:
            counter (int): Number of completed task units.
                Used in start_rendering()
            finished (bool): State that indicates that
                progress bar has completed
        '''
        self.size = size
        self.unit = unit
        self.prefix = prefix
        self.frames = frames
        self.timeout = timeout
        self.clearMode = clearMode
        #  Special variables
        self.frame = 0
        self.counter = 0
        self.finished = False

    def __enter__(self) -> "ProgressBar":
        self.renderingThread = threading.Thread(target=self.start_rendering)
        self.renderingThread.start()
        return self

    def __exit__(self, excType, excValue, traceback):
        self.finished = True
        self.renderingThread.join()

    def __repr__(self) -> str:
        return (
            "ProgressBar("
            f"size={self.size}, "
            f"unit=\"{self.unit}\", "
            f"prefix=\"{self.prefix}\", "
            f"frames=\"{self.frames}\", "
            f"timeout={self.timeout}, "
            f"clearMode={self.clearMode}"
            ")"
        )

    def render(self, counter: int) -> bool:
        '''
        Render progress bar

        Args:
            counter (int): Number of completed task units.
                If the counter is negative, then it is omitted

        Returns:
            bool: Should the next frame of the progress bar
                be rendered (equals to not finished)
        '''
        if counter >= 0:
            counter = f" {counter}"
        else:
            counter = ""

        if self.clearMode:
            end = "\n"
        else:
            end = "\r"

        if self.finished:
            end = "\n"
            self.frame = -1
        else:
            self.frame += 1
            self.frame %= len(self.frames) - 1

        print(
            f"{self.prefix}[{self.frames[self.frame] * self.size}]{counter} {self.unit}",
            end=end,
            flush=True
        )

        return not self.finished

    def start_rendering(self):
        '''
        Threading version of start_rendering

        Change counter and finished variables to control

        Might be unsafe without locks, but it shouldn't be
        If you change variables in one thread
        But if in several, then manage locks yourself
        '''
        change_cursor_visibility(False)
        while True:
            if not self.render(self.counter):
                break
            time.sleep(self.timeout)
            if self.clearMode:
                clear_screen(1)
        change_cursor_visibility(True)

    def start_rendering_mp(
        self,
        prefix: multiprocessing.Array,
        counter: multiprocessing.Value,
        unit: multiprocessing.Array,
        finished: multiprocessing.Value
    ):
        '''
        Multiprocessing version of start_rendering

        Create counter and finished as multiprocessing.Value
        and change them from MainProcess

        Args:
            prefix (multiprocessing.Array, 'c'): Prefix
            counter (multiprocessing.Value, 'i'): Counter
            unit (multiprocessing.Array, 'c'): Unit or postfix
            finished (multiprocessing.Value, 'b'): Finished
        '''
        change_cursor_visibility(False)
        while True:
            with (
                prefix.get_lock(),
                counter.get_lock(),
                unit.get_lock(),
                finished.get_lock()
            ):
                self.prefix = prefix.value.decode()
                self.counter = counter.value
                self.unit = unit.value.decode()
                self.finished = finished.value
            if not self.render(self.counter):
                break
            time.sleep(self.timeout)
            if self.clearMode:
                clear_screen(1)
        change_cursor_visibility(True)

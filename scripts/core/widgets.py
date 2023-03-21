'''
This file is part of 2trvl/dotfiles
Personal repository with scripts and configs
Which is released under MIT License
Copyright (c) 2022 Andrew Shteren
---------------------------------------------
             Widgets For Scripts             
---------------------------------------------
Dialog, input or options menu in a terminal
or dmenu (supported by dmenu, rofi).
Progress bar for an unknown process time

'''
import multiprocessing
import os
import threading
import time
from typing import TypeVar

from .common import WINDOWS_VT_MODE

USE_DMENU = os.environ.get("USE_DMENU", "False") == "True"


if os.name == "nt":
    import ctypes
    from ctypes import wintypes

    STD_OUTPUT_HANDLE = -11

    class CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
        '''
        Structure _CONSOLE_SCREEN_BUFFER_INFO from ConsoleApi2.h
        '''
        _fields_ = [
            ("dwSize",               wintypes._COORD),
            ("dwCursorPosition",     wintypes._COORD),
            ("wAttributes",          wintypes.WORD),
            ("srWindow",             wintypes._SMALL_RECT),
            ("dwMaximumWindowSize",  wintypes._COORD)
        ]

def clear_terminal(rows: int) -> bool:
    '''
    Clears terminal screen partially

    Args:
        rows (int): Rows number to clear

    Returns:
        bool: If function succeeds, the
        return value is True
    '''
    if os.name != "nt":
        print(f"\033[{rows}A \033[0J", end="\r")
        return True

    hConsoleOutput = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
    lpConsoleScreenBufferInfo = CONSOLE_SCREEN_BUFFER_INFO()

    if not ctypes.windll.kernel32.GetConsoleScreenBufferInfo(
        hConsoleOutput, ctypes.byref(lpConsoleScreenBufferInfo)
    ):
        return False

    lpConsoleScreenBufferInfo.dwCursorPosition.Y -= rows
    if not ctypes.windll.kernel32.SetConsoleCursorPosition(
        hConsoleOutput, lpConsoleScreenBufferInfo.dwCursorPosition
    ):
        return False

    if not ctypes.windll.kernel32.FillConsoleOutputCharacterA(
        hConsoleOutput,
        ctypes.c_char(b' '),
        lpConsoleScreenBufferInfo.dwSize.X * rows,
        lpConsoleScreenBufferInfo.dwCursorPosition,
        ctypes.byref(wintypes.DWORD(0))
    ):
        return False

    ctypes.windll.kernel32.FillConsoleOutputAttribute(
        hConsoleOutput,
        lpConsoleScreenBufferInfo.wAttributes,
        lpConsoleScreenBufferInfo.dwSize.X * rows,
        lpConsoleScreenBufferInfo.dwCursorPosition,
        ctypes.byref(wintypes.DWORD(0))
    )
    return True


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

    if WINDOWS_VT_MODE():
        #  Active console screen buffer
        STD_OUTPUT_HANDLE = -11

        class CONSOLE_CURSOR_INFO(ctypes.Structure):
            '''
            Structure CONSOLE_CURSOR_INFO from WinCon.h
            '''
            _fields_ = [
                ("size",     ctypes.c_int),
                ("visible",  ctypes.c_byte)
            ]

    else:
        #  ANSI escape sequences
        #  Part of common private modes
        ESC_HIDE_CURSOR = "\033[?25l"
        ESC_SHOW_CURSOR = "\033[?25h"

    def change_cursor_visibility(self, visibility: bool):
        '''
        Changes visibility of cursor in terminal

        Args:
            visibility (bool): Visibility of cursor.
                True to show, False to hide.
        '''
        if not WINDOWS_VT_MODE():
            ESC_CODE = (
                self.ESC_SHOW_CURSOR if visibility else self.ESC_HIDE_CURSOR
            )
            print(ESC_CODE, end="\r", flush=True)
            return

        hConsoleOutput = ctypes.windll.kernel32.GetStdHandle(
            self.STD_OUTPUT_HANDLE
        )
        lpConsoleCursorInfo = self.CONSOLE_CURSOR_INFO()

        if not ctypes.windll.kernel32.GetConsoleCursorInfo(
            hConsoleOutput, ctypes.byref(lpConsoleCursorInfo)
        ):
            return

        lpConsoleCursorInfo.visible = visibility
        ctypes.windll.kernel32.SetConsoleCursorInfo(
            hConsoleOutput, ctypes.byref(lpConsoleCursorInfo)
        )

    def start_rendering(self):
        '''
        Threading version of start_rendering

        Change counter and finished variables to control

        Might be unsafe without locks, but it shouldn't be
        If you change variables in one thread
        But if in several, then manage locks yourself
        '''
        self.change_cursor_visibility(False)
        while True:
            if not self.render(self.counter):
                break
            time.sleep(self.timeout)
            if self.clearMode:
                clear_terminal(1)
        self.change_cursor_visibility(True)

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
        self.change_cursor_visibility(False)
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
                clear_terminal(1)
        self.change_cursor_visibility(True)


def _show_terminal_dialog(question: str) -> bool | None:
    answer = input(f":: {question}? [Y/n] ")
    return _parse_dialog_answer(answer)

def _show_dmenu_dialog(question: str) -> bool | None:
    return False

def _parse_dialog_answer(value: str) -> bool | None:
    '''
    Parses dialog answer

    Args:
        value (str): User answer

    Returns:
        bool | None: If is positive returns True,
            if not False, if the answer is not clear None
    '''
    value = value.lower()

    if value in ["yes", "y", "да"]:
        return True

    elif value in ["no", "n", "нет"]:
        return False

    return None

def show_dialog(question: str) -> bool:
    '''
    Displays a dialog based on the USE_DMENU
    environment variable

    Args:
        question (str): Closed-ended question

    Returns:
        bool: True for positive and False for
            negative answer
    '''
    while True:
        if USE_DMENU:
            answer = _show_dmenu_dialog(question)
            if answer is None:
                continue
        else:
            answer = _show_terminal_dialog(question)
            if answer is None:
                clear_terminal(1)
                continue

        return answer


T = TypeVar('T')

def _show_terminal_input(prompt: str, valueType: T) -> T:
    return valueType(input(f"{prompt}:\n> "))

def _show_dmenu_input(prompt: str, valueType: T) -> T:
    return valueType()

def show_input(prompt: str, valueType: T) -> T:
    '''
    Displays an input based on the USE_DMENU
    environment variable

    Args:
        prompt (str): Input message or CTA
        valueType (T): The type of value to return

    Returns:
        T: Value of valueType
    '''
    while True:
        try:
            if USE_DMENU:
                return _show_dmenu_input(prompt, valueType)
            return _show_terminal_input(prompt, valueType)
        except ValueError:
            if not USE_DMENU:
                clear_terminal(2)


def _show_terminal_menu(
    prompt: str, items: list[str], indentSize: int = 2
) -> set[int]:
    print(f"{prompt} (0,1,2,0-2):")

    for index, item in enumerate(items):
        print(f"{' ' * indentSize}{index}. {item}")

    selection = input("> ")
    return _parse_menu_selection(selection, index)

def _show_dmenu_menu(prompt: str, items: list[str]) -> set[int]:
    return set()

def _parse_menu_selection(selection: str, maxValue: int) -> set[int]:
    '''
    Parses menu selection

    Args:
        selection (str): Selection in format
            0,1,2,0-2
        maxValue (int): Selection range limit

    Returns:
        set[int]: Set of selected options
            {0, 1, 2}
    '''
    selection = selection.split(",")
    indexes = set()

    for slice in selection:
        if slice.startswith("-"):
            raise ValueError
        if slice.isnumeric():
            if int(slice) > maxValue:
                raise ValueError
            indexes.add(int(slice))
        else:
            slice = slice.split("-")
            if int(slice[0]) > maxValue or int(slice[-1]) > maxValue:
                raise ValueError
            indexes.update(range(int(slice[0]), int(slice[-1]) + 1))

    return indexes

def show_menu(prompt: str, items: list[str]) -> set[int]:
    '''
    Displays a menu based on the USE_DMENU
    environment variable

    Args:
        prompt (str): Menu title or CTA
        items (list[str]): Items to choose

    Returns:
        list[int]: Indexes of selected items
    '''
    while True:
        try:
            if USE_DMENU:
                return _show_dmenu_menu(prompt, items)
            return _show_terminal_menu(prompt, items)
        except ValueError:
            if not USE_DMENU:
                clear_terminal(2 + len(items))

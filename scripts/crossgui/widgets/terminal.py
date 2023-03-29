'''
This file is part of 2trvl/crossgui
Common widgets between different environments
Which is released under BSD-2-Clause license
Copyright (c) 2023 Andrew Shteren
---------------------------------------------
            Terminal Specific Code           
---------------------------------------------
Clear screen, open alternate screen buffer,
print with color, move and hide cursor.
Replaces colorama and is successor of
2trvl/xamalk

'''
import os

from .runtime import WINDOWS_VT_MODE


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

def clear_screen(rows: int) -> bool:
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


if not WINDOWS_VT_MODE():
    #  ANSI escape sequences
    #  Part of common private modes
    ESC_HIDE_CURSOR = "\033[?25l"
    ESC_SHOW_CURSOR = "\033[?25h"
else:
    class CONSOLE_CURSOR_INFO(ctypes.Structure):
        '''
        Structure CONSOLE_CURSOR_INFO from WinCon.h
        '''
        _fields_ = [
            ("dwSize",    wintypes.DWORD),
            ("bVisible",  wintypes.BOOL)
        ]

def change_cursor_visibility(visibility: bool):
    '''
    Changes visibility of cursor in terminal

    Args:
        visibility (bool): Visibility of cursor.
            True to show, False to hide.
    '''
    if not WINDOWS_VT_MODE():
        ESC_CODE = (
            ESC_SHOW_CURSOR if visibility else ESC_HIDE_CURSOR
        )
        print(ESC_CODE, end="\r", flush=True)
        return

    hConsoleOutput = ctypes.windll.kernel32.GetStdHandle(
        STD_OUTPUT_HANDLE
    )
    lpConsoleCursorInfo = CONSOLE_CURSOR_INFO()

    if not ctypes.windll.kernel32.GetConsoleCursorInfo(
        hConsoleOutput, ctypes.byref(lpConsoleCursorInfo)
    ):
        return

    lpConsoleCursorInfo.bVisible = visibility
    ctypes.windll.kernel32.SetConsoleCursorInfo(
        hConsoleOutput, ctypes.byref(lpConsoleCursorInfo)
    )

'''
This file is part of 2trvl/crossgui
Common widgets between different environments
Which is released under BSD-2-Clause license
Copyright (c) 2022 Andrew Shteren
---------------------------------------------
          Environment Determination          
---------------------------------------------
Windows terminal ANSI codes support. Auto and
manual choice of environment: terminal, dmenu
(supported by dmenu, rofi) and qt

'''
import enum
import functools
import platform
import sys

from shutil import which


class Environment(enum.IntEnum):
    Dmenu = enum.auto()
    Qt = enum.auto()
    Rofi = enum.auto()
    Terminal = enum.auto()
    Undefined = enum.auto()

graphics = Environment.Undefined

def use_graphics(environment: Environment):
    '''
    Change environment manually

    Args:
        graphics (Environment): GUI choice
    '''
    global graphics
    graphics = environment

def _use_available_graphics():
    '''
    Search for graphics available on the device
    and select it to display widgets
    
    This function is called automatically
    if use_graphics() was not called before
    displaying first widget
    '''
    global graphics

    if sys.stdin and sys.stdin.isatty():
        graphics = Environment.Terminal
    elif which("dmenu") is not None:
        graphics = Environment.Dmenu
    elif which("rofi") is not None:
        graphics = Environment.Rofi
    else:
        graphics = Environment.Qt


@functools.cache
def WINDOWS_VT_MODE() -> bool:
    '''
    Determines if Windows API needed
    or ANSI escape codes are available

    Starting from Windows 10 TH2 (v1511),
    cmd.exe support ANSI Escape Sequences,
    but they must be enabled

    It can't be used for cursor positioning.
    Because cursor movement using ansi escape
    codes on Windows will be bounded by the
    current viewport into the buffer. Scrolling
    (if available) will not occur.
    '''
    if platform.system() == "Windows":
        version = platform.win32_ver()[1]
        version = tuple(int(num) for num in version.split("."))

        if version < (10, 0, 10586):
            return True

        import ctypes

        STD_OUTPUT_HANDLE = -11
        INVALID_HANDLE_VALUE = -1
        hConsoleOutput = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
        if hConsoleOutput == INVALID_HANDLE_VALUE:
            return True

        dwMode = ctypes.c_ulong(0)
        if not ctypes.windll.kernel32.GetConsoleMode(
            hConsoleOutput, ctypes.byref(dwMode)
        ):
            return True

        ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004

        #  Check if vt processing is already enabled
        if dwMode.value & ENABLE_VIRTUAL_TERMINAL_PROCESSING:
            return False

        dwMode.value |= ENABLE_VIRTUAL_TERMINAL_PROCESSING
        if not ctypes.windll.kernel32.SetConsoleMode(
            hConsoleOutput, dwMode.value
        ):
            return True

        import atexit

        def disable_vt_processing():
            dwMode.value &= ~ENABLE_VIRTUAL_TERMINAL_PROCESSING
            ctypes.windll.kernel32.SetConsoleMode(hConsoleOutput, dwMode.value)

        atexit.register(disable_vt_processing)

    return False

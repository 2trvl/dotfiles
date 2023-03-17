'''
This file is part of 2trvl/dotfiles
Personal repository with scripts and configs
Which is released under MIT License
Copyright (c) 2022 Andrew Shteren
---------------------------------------------
             Scripts Common Parts            
---------------------------------------------
Code that cannot be attributed to anything in
particular and is used in several scripts

'''
import functools
import platform

#  Characters not allowed in file names
charsForbidden = {
    "<":  "",
    ">":  "",
    ":":  "",
    "\"": "",
    "/":  "",
    "\\": "",
    "|":  "",
    "?":  "",
    "*":  ""
}
charsForbidden = str.maketrans(charsForbidden)


@functools.cache
def WINDOWS_VT_MODE() -> bool:
    '''
    Determines if ANSI escape codes
    are available or Windows API needed

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
            hConsoleOutput,
            ctypes.byref(dwMode)
        ): return True

        ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004

        # check if vt processing is already enabled
        if dwMode.value & ENABLE_VIRTUAL_TERMINAL_PROCESSING:
            return False
        
        dwMode.value |= ENABLE_VIRTUAL_TERMINAL_PROCESSING
        if not ctypes.windll.kernel32.SetConsoleMode(
            hConsoleOutput,
            dwMode.value
        ): return True

        import atexit

        def disable_vt_processing():
            dwMode.value &= ~ENABLE_VIRTUAL_TERMINAL_PROCESSING
            ctypes.windll.kernel32.SetConsoleMode(
                hConsoleOutput,
                dwMode.value
            )

        atexit.register(disable_vt_processing)

    return False


def run_as_admin():
    '''
    Exit with code 126 to have start.bat
    restart the script with elevated privileges
    if necessary
    '''
    if platform.system() != "Windows":
        import os
        isAdmin = os.getuid() == 0
    else:
        import ctypes
        isAdmin = ctypes.windll.shell32.IsUserAnAdmin() == True
    
    if not isAdmin:
        import sys
        sys.exit(126)

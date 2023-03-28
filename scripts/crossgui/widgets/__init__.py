'''
This file is part of 2trvl/crossgui
Common widgets between different environments
Which is released under BSD-2-Clause license
Copyright (c) 2022 Andrew Shteren
---------------------------------------------
             Widgets For Scripts             
---------------------------------------------
Dialog, input or options menu in a terminal,
dmenu (supported by dmenu, rofi) or qt.
Progress bar for an unknown process time

'''
from .dialog import show_dialog
from .field import show_input
from .menu import show_menu
from .progressbar import ProgressBar

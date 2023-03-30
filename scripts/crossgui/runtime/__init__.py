'''
This file is part of 2trvl/crossgui
Common widgets between different environments
Which is released under BSD-2-Clause license
Copyright (c) 2022 Andrew Shteren
---------------------------------------------
          Environment Determination          
---------------------------------------------
Auto and manual choice of environment:
terminal, dmenu, rofi and qt

'''
__all__ = ("terminal", "Environment", "use_graphics")

import enum
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

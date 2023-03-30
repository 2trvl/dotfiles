'''
This file is part of 2trvl/crossgui
Common widgets between different environments
Which is released under BSD-2-Clause license
Copyright (c) 2023 Andrew Shteren
---------------------------------------------
                    Field                    
---------------------------------------------
Create generic or password input field

'''
from typing import TypeVar

from .. import runtime
from ..runtime import Environment
from ..runtime.terminal import clear_screen

T = TypeVar('T')


def _show_terminal_input(prompt: str, valueType: T) -> T:
    return valueType(input(f"{prompt}:\n> "))


def _show_dmenu_input(prompt: str, valueType: T) -> T:
    return valueType()


def show_input(prompt: str, valueType: T) -> T:
    '''
    Displays an input based on runtime.graphics

    Args:
        prompt (str): Input message or CTA
        valueType (T): The type of value to return

    Returns:
        T: Value of valueType
    '''
    if runtime.graphics is Environment.Undefined:
        runtime._use_available_graphics()

    while True:
        try:
            if runtime.graphics is Environment.Dmenu:
                return _show_dmenu_input(prompt, valueType)
            elif runtime.graphics is Environment.Terminal:
                return _show_terminal_input(prompt, valueType)
        except ValueError:
            if runtime.graphics is Environment.Terminal:
                clear_screen(2)

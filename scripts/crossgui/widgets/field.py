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

from .environment import USE_DMENU
from .terminal import clear_screen

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
                clear_screen(2)

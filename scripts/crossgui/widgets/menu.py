'''
This file is part of 2trvl/crossgui
Common widgets between different environments
Which is released under BSD-2-Clause license
Copyright (c) 2023 Andrew Shteren
---------------------------------------------
                     Menu                    
---------------------------------------------
Create a menu with a choice of one or
multiple options

'''
from .. import runtime
from ..runtime import Environment
from ..runtime.terminal import clear_screen


def _show_terminal_menu(
    prompt: str,
    items: list[str],
    one: bool = False,
    indentSize: int = 2
) -> list[int]:
    print(prompt)

    for index, item in enumerate(items):
        print(f"{' ' * indentSize}{index}. {item}")

    selection = input("> ")
    return _parse_menu_selection(selection, index, one)


def _show_rofi_menu(
    prompt: str,
    items: list[str],
    one: bool = False
) -> list[int]:
    return []


def _parse_menu_selection(
    selection: str,
    maxValue: int,
    one: bool
) -> list[int]:
    '''
    Parses menu selection

    Args:
        selection (str): Selection in format
            0,1,2,0-2
        maxValue (int): Selection range limit
        one (bool): Selection must contain
            only one option or not

    Returns:
        list[int]: List of selected options
            [0, 1, 2]
    '''
    selection = selection.split(",")
    indexes = set()

    for slice in selection:
        if slice.startswith("-"):
            raise ValueError
        elif slice.isnumeric():
            if int(slice) > maxValue:
                raise ValueError
            indexes.add(int(slice))
        else:
            slice = slice.split("-")
            if int(slice[0]) > maxValue or int(slice[-1]) > maxValue:
                raise ValueError
            indexes.update(range(int(slice[0]), int(slice[-1]) + 1))

    if one and len(indexes) != 1:
        raise ValueError
    
    return sorted(indexes)


def show_menu(
    prompt: str,
    items: list[str],
    one: bool = False
) -> list[int]:
    '''
    Displays a menu based on runtime.graphics

    Args:
        prompt (str): Menu title or CTA
        items (list[str]): Items to choose
        one (bool): Only one option can be
            selected. Defaults to False.

    Returns:
        list[int]: Indexes of selected items
    '''
    if runtime.graphics is Environment.Undefined:
        runtime._use_available_graphics()

    if one:
        prompt = f"{prompt} (Choose one option):"
    else:
        prompt = f"{prompt} (0,1,2,0-2):"

    while True:
        try:
            if runtime.graphics is Environment.Rofi:
                return _show_rofi_menu(prompt, items, one)
            elif runtime.graphics is Environment.Terminal:
                return _show_terminal_menu(prompt, items, one)
        except ValueError:
            if runtime.graphics is Environment.Terminal:
                clear_screen(2 + len(items))

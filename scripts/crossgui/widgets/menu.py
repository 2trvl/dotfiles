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
from .environment import USE_DMENU
from .terminal import clear_screen


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
                clear_screen(2 + len(items))

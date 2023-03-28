'''
This file is part of 2trvl/crossgui
Common widgets between different environments
Which is released under BSD-2-Clause license
Copyright (c) 2023 Andrew Shteren
---------------------------------------------
                    Dialog                   
---------------------------------------------
Create yes/no dialog and get answer back

'''
from .environment import USE_DMENU
from .terminal import clear_screen


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
                clear_screen(1)
                continue

        return answer

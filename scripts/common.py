'''
This file is part of 2trvl/dotfiles
Personal repository with scripts and configs
Which is released under MIT license
Copyright (c) 2022 Andrew Shteren
--------------------------------------------
            Scripts Common Parts            
--------------------------------------------
My task is to make the scripts as
independent as possible. Therefore, these
parts are used in places that imply presence
of other scripts. If this cannot be
guaranteed, the functions have counterparts
inside the script

'''
import os


def run_as_admin():
    '''
    Exit with code 126 to have start.bat
    restart the script with elevated privileges
    if necessary
    '''
    if os.name != "nt":
        isAdmin = os.getuid() == 0
    else:
        import ctypes
        isAdmin = ctypes.windll.shell32.IsUserAnAdmin() == True

    if not isAdmin:
        import sys
        sys.exit(126)

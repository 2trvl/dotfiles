'''
This file is part of 2trvl/dotfiles
Personal repository with scripts and configs
Which is released under MIT license
Copyright (c) 2022 Andrew Shteren
--------------------------------------------
            Scripts Common Parts            
--------------------------------------------
Code that cannot be attributed to anything
in particular and is used in several scripts

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

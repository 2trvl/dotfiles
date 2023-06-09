'''
This file is part of 2trvl/dotfiles
Personal repository with scripts and configs
Which is released under MIT license
Copyright (c) 2023 Andrew Shteren
--------------------------------------------
             Scripts Entry Point            
--------------------------------------------
Scans subdirectories, finds all Python
scripts and executes the source code of the
selected one. Pass as an argument path to a
temporary file for writing the selected
script name, rather than executing it

'''
if __name__ == "__main__":
    import os
    import sys
    from crossgui.widgets import show_menu

    ignore = {
        "dirs": {
            ".git",
            "__pycache__",
            "crossgui",
            "venv"
        },
        "files": {
            "__init__.py",
            "__main__.py",
            "common.py"
        }
    }
    scripts = []

    scriptsFolder = os.path.abspath(__file__)
    scriptsFolder = os.path.dirname(scriptsFolder)

    for root, dirs, files in os.walk(scriptsFolder, topdown=True):
        dirs[:] = set(dirs) - ignore["dirs"]
        files = set(files) - ignore["files"]
        
        for file in files:
            if file.endswith(".py"):
                file = os.path.join(root, file)
                file = os.path.relpath(file, scriptsFolder)
                scripts.append(file)
    
    scripts.sort()
    
    script = show_menu("Script to run", scripts, True)[0]
    script = scripts[script]
    
    if len(sys.argv) != 1:
        with open(sys.argv[1], "w", encoding="utf-8") as temp:
            temp.write(script)
    else:
        script = os.path.join(scriptsFolder, script)
        with open(script, encoding="utf-8") as code:
            sys.argv[0] = os.path.basename(script)
            exec(code.read())

: #   ______   ______  ______   ______  ______       ______   ______   ______ 
: #  /\  ___\ /\__  _\/\  __ \ /\  == \/\__  _\     /\  == \ /\  __ \ /\__  _\
: #  \ \___  \\/_/\ \/\ \  __ \\ \  __<\/_/\ \/  __ \ \  __< \ \  __ \\/_/\ \/
: #   \/\_____\  \ \_\ \ \_\ \_\\ \_\ \_\ \ \_\ /\_\ \ \_____\\ \_\ \_\  \ \_\
: #    \/_____/   \/_/  \/_/\/_/ \/_/ /_/  \/_/ \/_/  \/_____/ \/_/\/_/   \/_/
: #
: # Cross-platform way to run python in virtual environment
: #
: # Just use it like this:
: # start.bat archiver.py args
: # Or any other python script in the folder
: #
: # ------------------------------ Features ----------------------------------
: #
: # Creates a virtual environment based on requirements.txt, which is located
: # in the same folder
: #
: # Loads environment variables from .env file if it exists
: #
: # You can add script selector __main__.py which will write the script name
: # to /tmp/getscript.tmp. Then it will be possible to run start.bat without
: # arguments
: #
: # Requests administrator rights if needed, Polkit is used in Linux, VBScript
: # in Windows and AppleScript in OS X. Python interpreter has only two
: # standard codes 0 and 1. But you can set the exit code manually with
: # sys.exit. Use code 126 to have start.bat restart script with admin rights.
: # Example "except PermissionError: sys.exit(126)"
: #
: # It is also possible to upgrade requirements with:
: # start.bat --upgrade
: #
: # -------------------------- Syntax reference ------------------------------
: #
: # Colon in batch means label declaration, in POSIX shell it is equivalent to
: # true. A feature of COMMAND.COM is that it skips labels that it cannot
: # jump to. Label becomes unusable if it contains special characters. Thus,
: # inside a batch script, you can add a shell line with ":;". Cross-platform
: # comment is added using ":;#" or ": #". The space or semicolon are
: # necessary because sh considers # to be part of a command name if it is not
: # the first character of an identifier.
: #
: # For batch code blocks, heredocs can be used. This redirection mechanism is
: # for passing multiple lines of input to a command or to comment out code.
: # Once again use the colon trick to ignore this line in batch. Put the
: # delimiting identifier in quotes so shell does not interpret its contents.
: # Identifier is also an unused batch label for closing line to be ignored.
: # In this way shell treats batch code as an unused string, and cmd
: # executes it.
: #
: # DOS uses carriage return and line feed "\r\n" as a line ending, which Unix
: # uses just line feed "\n". So in order for script to run you may need to
: # convert end of line sequences with dos2unix or a text editor. Although on
: # Windows 10 start.bat runs without error with unix-style line endings.

:<<"::Batch"
    @echo off
    setlocal EnableDelayedExpansion

    for /f "tokens=2 delims=:" %%i in ('chcp') do (
        set codepage=%%i
        if "!codepage:~-1!"=="." (
            set codepage=!codepage:~1,-1!
        ) else (
            set codepage=!codepage:~1!
        )
    )
    chcp 65001 > nul

    set filepath=%~dp0

    if not exist "%filepath%venv\" (
        echo First run, creating a virtual environment..
        python -m venv "%filepath%venv" --upgrade-deps > nul
        call "%filepath%venv\Scripts\activate.bat"
        pip install -r "%filepath%requirements.txt" --quiet --use-pep517
    ) else (
        call "%filepath%venv\Scripts\activate.bat"
    )

    if exist "%filepath%.env" (
        for /f "tokens=* eol=#" %%i in ('type "%filepath%.env"') do set %%i
    )

    if "%~1"=="" (
        if exist "%filepath%__main__.py" (
            python "%filepath%__main__.py" "%temp%\getscript.tmp"
            set /p script=<"%temp%\getscript.tmp"
            del "%temp%\getscript.tmp"
            "%~f0" "!script!"
        ) else (
            echo Specify the script to be executed
        )
    ) else (
        if not exist "%filepath%%~1" (
            if /i "%~1"=="-u" (
                goto upgrade
            )
            if /i "%~1"=="--upgrade" (
                goto upgrade
            )
            if /i "%~1"=="-h" (
                goto help
            )
            if /i "%~1"=="--help" (
                goto help
            )
            goto script-not-found

            :upgrade
            python -m pip install --upgrade pip
            pip install -r "%filepath%requirements.txt" --upgrade --use-pep517
            goto exit

            :help
            echo|set /p dumb="Usage: start.bat [script [arguments..]] [-u | -h]" & echo:
            echo:
            echo:Python Virtual Environment Utility
            echo:
            echo|set /p dumb="Positional arguments:" & echo:
            echo:script           script path in the utility folder
            echo:arguments        arguments of the script to run
            echo:
            echo|set /p dumb="Utility options (used when not running scripts):" & echo:
            echo:-u, --upgrade    update outdated dependencies
            echo:-h, --help       show this help message and exit
            goto exit
            
            :script-not-found
            echo No script named "%1"
            goto exit
        ) else (
            set args=%*
            call set args=%%args:*%1=%%
            python "%filepath%%~1" !args!
            if errorlevel==126 (
                echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
                echo UAC.ShellExecute "cmd.exe", "/k cd /d ""%cd%"" & cls & ""%~s0"" ""%~1"" !args!", "", "runas", 1 >> "%temp%\getadmin.vbs"
                "%temp%\getadmin.vbs"
                del "%temp%\getadmin.vbs"
            )
        )
    )

    :exit
    chcp %codepage% > nul
    deactivate
    endlocal
    exit /b
::Batch

filepath=$(cd -- $(dirname "$0") >/dev/null 2>&1; pwd -P)

if [ ! -d "$filepath/venv" ]; then
    printf "\033[?25lFirst run, creating a virtual environment..\r"
    python -m venv "$filepath/venv" --upgrade-deps > /dev/null
    . "$filepath/venv/bin/activate"
    pip install -r "$filepath/requirements.txt" --quiet --use-pep517
    printf "\033[2K\033[?25h"
else
    . "$filepath/venv/bin/activate"
fi

if [ -f "$filepath/.env" ]; then
    export $(grep -v "^#" "$filepath/.env" | xargs -d "\n")
fi

if [ -z "$1" ]; then
    if [ -f "$filepath/__main__.py" ]; then
        python "$filepath/__main__.py" /tmp/getscript.tmp
        script=$(cat /tmp/getscript.tmp)
        rm /tmp/getscript.tmp
        "$0" "$script"
    else
        echo "Specify the script to be executed"
    fi
elif [ ! -f "$filepath/$1" ]; then
    case $1 in
        -u|--upgrade)
            python -m pip install --upgrade pip
            pip install -r "$filepath/requirements.txt" --upgrade --use-pep517
            ;;
        -h|--help)
            echo "Usage: start.bat [script [arguments..]] [-u | -h]"
            echo
            echo "Python Virtual Environment Utility"
            echo
            echo "Positional arguments:"
            echo "script           script path in the utility folder"
            echo "arguments        arguments of the script to run"
            echo
            echo "Utility options (used when not running scripts):"
            echo "-u, --upgrade    update outdated dependencies"
            echo "-h, --help       show this help message and exit"
            ;;
        *)
            echo "No script named \"$1\""
            ;;
    esac
else
    script="$1"
    shift
    python "$filepath/$script" "$@"
    if [ $? -eq 126 ]; then
        eval "pkexec env $(env | awk -F '=' '{if (NR!="1") printf " "; printf $1 "='\''"; for (i=2; i<NF; i++) printf $i "="; printf $NF "'\''"}') python '$filepath/$script' '$@'"
    fi
fi

if [ -f "$filepath/.env" ]; then
    unset $(grep -v "^#" "$filepath/.env" | sed -E "s/(.*)=.*/\1/" | xargs)
fi

deactivate

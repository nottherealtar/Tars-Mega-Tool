@echo off
:: Enhanced Compiler Script for Tars Utilities Tool with Versioning

:: Configuration
set PROJECT_NAME=TarsUtilitiesTool
set MAIN_SCRIPT=main.py
set ICON_PATH=logoico.ico
set VERSION_FILE=VERSION.txt
set PYINSTALLER_OPTIONS=--onefile --console --noconfirm --clean
set PROJECT_DESCRIPTION=This is a Tars Utilities Tool for various system-based tasks.

:: Read Version from File
if not exist %VERSION_FILE% (
    echo Error: Version file "%VERSION_FILE%" not found. Exiting...
    pause
    exit /b 1
)
set /p VERSION=<%VERSION_FILE%
set OUTPUT_NAME=%PROJECT_NAME%_v%VERSION%.exe

:: Welcome Message
echo ===========================================================
echo Compiling %PROJECT_NAME% (Version: %VERSION%)...
echo ===========================================================

:: Ensure pyinstaller is installed
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo PyInstaller is not installed. Installing it now...
    pip install pyinstaller
    if %errorlevel% neq 0 (
        echo Failed to install PyInstaller. Exiting...
        pause
        exit /b 1
    )
)

:: Check if the main script exists
if not exist %MAIN_SCRIPT% (
    echo Error: Main script "%MAIN_SCRIPT%" not found. Exiting...
    pause
    exit /b 1
)

:: Check if the icon file exists
if not exist %ICON_PATH% (
    echo Warning: Icon file "%ICON_PATH%" not found. Using default PyInstaller icon.
    set ICON_OPTION=
) else (
    set ICON_OPTION=--icon=%ICON_PATH%
)

:: Compile the project
echo ===========================================================
echo Compiling with PyInstaller...
echo ===========================================================
pyinstaller %PYINSTALLER_OPTIONS% %ICON_OPTION% --name=%PROJECT_NAME%_v%VERSION% %MAIN_SCRIPT%

:: Check if the executable was created
if exist dist\%OUTPUT_NAME% (
    move dist\%OUTPUT_NAME% . >nul
    echo ===========================================================
    echo Compilation successful! Executable created: %OUTPUT_NAME%
    echo ===========================================================
) else (
    echo ===========================================================
    echo Compilation failed. Check the output for errors.
    echo ===========================================================
    pause
    exit /b 1
)

:: Clean up build artifacts
echo Cleaning up build artifacts...
rmdir /s /q build >nul 2>&1
del %PROJECT_NAME%_v%VERSION%.spec >nul 2>&1
rmdir /s /q dist >nul 2>&1

:: Completion Message
echo ===========================================================
echo Compilation process completed!
echo Your executable is ready: %OUTPUT_NAME%
echo ===========================================================
pause
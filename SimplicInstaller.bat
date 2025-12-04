@echo off
setlocal

:: Step 1: Define paths
set "DESKTOP=%USERPROFILE%\Desktop"
set "ONEFILE=%DESKTOP%\ONEFILE"
set "LIBS=%ONEFILE%\libs"
set "PYINSTALLER_URL=https://github.com/pyinstaller/pyinstaller/archive/refs/heads/develop.zip"
set "EDITOR_URL=https://raw.githubusercontent.com/OftenNotKnown/SimplicIDLE/main/main.py"
set "MAIN_PATH=%ONEFILE%\main.py"
set "SHORTCUT_NAME=SimplicEditor.lnk"
set "EXE_PATH=%ONEFILE%\dist\main.exe"
set "VBS=%TEMP%\shortcut.vbs"

:: Step 2: Create folders
echo 🛠 Creating folders...
mkdir "%ONEFILE%" >nul 2>&1
mkdir "%LIBS%" >nul 2>&1

:: Step 3: Download PyInstaller source
echo ⬇️ Downloading PyInstaller...
powershell -Command "Invoke-WebRequest -Uri '%PYINSTALLER_URL%' -OutFile '%LIBS%\pyinstaller.zip'"

:: Step 4: Download editor source (main.py)
echo ⬇️ Downloading editor source...
powershell -Command "Invoke-WebRequest -Uri '%EDITOR_URL%' -OutFile '%MAIN_PATH%'"

:: Step 5: Extract PyInstaller
echo 📦 Extracting PyInstaller...
powershell -Command "Expand-Archive -Path '%LIBS%\pyinstaller.zip' -DestinationPath '%LIBS%'"

:: Step 6: Install PyInstaller via python
echo 🧠 Installing PyInstaller...
pushd "%LIBS%\pyinstaller-develop"
python setup.py install
popd

:: Step 7: Use PyInstaller to compile main.py
echo 🛠 Compiling SimplicEditor into EXE...
pushd "%ONEFILE%"
pyinstaller main.py --onefile
popd

:: Step 8: Create desktop shortcut
echo 🔗 Creating desktop shortcut...
> "%VBS%" echo Set oWS = WScript.CreateObject("WScript.Shell")
>> "%VBS%" echo sLinkFile = oWS.SpecialFolders("Desktop") ^& "\%SHORTCUT_NAME%"
>> "%VBS%" echo Set oLink = oWS.CreateShortcut(sLinkFile)
>> "%VBS%" echo oLink.TargetPath = "%EXE_PATH%"
>> "%VBS%" echo oLink.WorkingDirectory = "%ONEFILE%"
>> "%VBS%" echo oLink.IconLocation = "%EXE_PATH%, 0"
>> "%VBS%" echo oLink.Save
cscript //nologo "%VBS%"
del "%VBS%"

:: Step 9: Done
echo ✅ SimplicEditor installed and shortcut created.
pause

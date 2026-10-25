@echo off
rem Start the CodeDNA IDE (Windows).
rem   start.bat            opens a demo project (created on first run in %USERPROFILE%\codedna-demo)
rem   start.bat C:\path    opens that folder instead
rem The first run installs and builds the IDE, which takes several minutes.
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\codedna.exe" (
    echo The CodeDNA core is not installed in .venv. Run these once, then start.bat again:
    echo   python -m venv .venv
    echo   .venv\Scripts\python -m pip install -e ".[ml,api,dev]"
    exit /b 1
)
rem The IDE starts "codedna serve" itself; point it at the project venv.
set "CODEDNA_EXECUTABLE=%~dp0.venv\Scripts\codedna.exe"

rem Java support in the editor needs a JDK. Use the portable JDK if one is
rem recorded; otherwise keep whatever JAVA_HOME is already set.
set "TOOLS_JSON=%USERPROFILE%\.codex\tools\java-maven.json"
if exist "%TOOLS_JSON%" (
    for /f "usebackq delims=" %%j in (`powershell -NoProfile -Command "(Get-Content -Raw '%TOOLS_JSON%' | ConvertFrom-Json).java_home"`) do set "JAVA_HOME=%%j"
    for /f "usebackq delims=" %%m in (`powershell -NoProfile -Command "(Get-Content -Raw '%TOOLS_JSON%' | ConvertFrom-Json).maven_home"`) do set "MAVEN_HOME=%%m"
)
if defined JAVA_HOME set "PATH=%JAVA_HOME%\bin;%PATH%"
if defined MAVEN_HOME set "PATH=%MAVEN_HOME%\bin;%PATH%"
if not defined JAVA_HOME echo Note: no JDK found, so Java code completion will not start. CodeDNA itself still works.

set "TARGET=%~1"
if "%TARGET%"=="" (
    set "TARGET=%USERPROFILE%\codedna-demo"
    if not exist "%USERPROFILE%\codedna-demo" (
        echo Creating the demo project in %USERPROFILE%\codedna-demo ...
        ".venv\Scripts\python" scripts\make_demo_repo.py "%USERPROFILE%\codedna-demo" || exit /b 1
    )
)

cd ide
if not exist "node_modules" (
    echo Installing the IDE, first run only ...
    call npm install || exit /b 1
)
if not exist "electron-app\lib\backend\main.js" (
    echo Building the IDE, first run only ...
    call npm run build || exit /b 1
)

echo Starting the CodeDNA IDE on %TARGET%
echo Keep this window open while you use the IDE; closing it closes the IDE.
cd electron-app
call "..\node_modules\.bin\theia.cmd" start "%TARGET%"

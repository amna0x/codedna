@echo off
rem Start the CodeDNA IDE (Windows).
rem   start.bat            opens a demo project (created on first run in %USERPROFILE%\codedna-demo)
rem   start.bat C:\path    opens that folder instead
rem The first run installs and builds the IDE, which takes several minutes;
rem it builds again after a pull that changed the IDE.
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\codedna.exe" (
    echo The CodeDNA core is not installed in .venv. Run these once, then start.bat again:
    echo   python -m venv .venv
    echo   .venv\Scripts\python -m pip install -e ".[ml,api,dev]"
    echo   .venv\Scripts\python -m pip install -e plugins\codedna-java -e plugins\codedna-python
    exit /b 1
)
rem Java and Python support are the codedna-java (D-054) and codedna-python
rem (D-060) plugins. Install each once from this checkout, so an older .venv
rem keeps working after the pull that added it.
if not exist ".venv\Lib\site-packages\codedna_java-*.dist-info" (
    echo Installing the Java plugin from plugins\codedna-java ...
    call ".venv\Scripts\python" -m pip install --disable-pip-version-check -e plugins\codedna-java || exit /b 1
)
if not exist ".venv\Lib\site-packages\codedna_python-*.dist-info" (
    echo Installing the Python plugin from plugins\codedna-python ...
    call ".venv\Scripts\python" -m pip install --disable-pip-version-check -e plugins\codedna-python || exit /b 1
)
rem The IDE starts "codedna serve" itself; point it at the project venv.
set "CODEDNA_EXECUTABLE=%~dp0.venv\Scripts\codedna.exe"
rem The History replay view (Ctrl+Shift+Alt+R) opens the study results in this checkout.
set "CODEDNA_REPLAY_FOLDERS=%~dp0experiments\results\replay-2026-10-25;%~dp0experiments\results\study11-2026-10-21"

rem Java support in the editor needs a JDK. Use the portable JDK if one is
rem recorded; otherwise keep whatever JAVA_HOME is already set.
set "TOOLS_JSON=%USERPROFILE%\.codex\tools\java-maven.json"
if exist "%TOOLS_JSON%" (
    for /f "usebackq delims=" %%j in (`powershell -NoProfile -Command "(Get-Content -LiteralPath $env:TOOLS_JSON -Raw | ConvertFrom-Json).java_home"`) do set "JAVA_HOME=%%j"
    for /f "usebackq delims=" %%m in (`powershell -NoProfile -Command "(Get-Content -LiteralPath $env:TOOLS_JSON -Raw | ConvertFrom-Json).maven_home"`) do set "MAVEN_HOME=%%m"
)
if defined JAVA_HOME set "PATH=%JAVA_HOME%\bin;%PATH%"
if defined MAVEN_HOME set "PATH=%MAVEN_HOME%\bin;%PATH%"
rem Reuse the portable Gradle runtime and cache when one has been installed.
set "GRADLE_TOOLS_JSON=%USERPROFILE%\.codex\tools\gradle\runtime.json"
if exist "%GRADLE_TOOLS_JSON%" (
    for /f "usebackq delims=" %%g in (`powershell -NoProfile -Command "(Get-Content -LiteralPath $env:GRADLE_TOOLS_JSON -Raw | ConvertFrom-Json).home"`) do set "GRADLE_HOME=%%g"
    if not defined GRADLE_USER_HOME set "GRADLE_USER_HOME=%USERPROFILE%\.codex\tools\gradle\cache"
)
if defined GRADLE_HOME set "PATH=%GRADLE_HOME%\bin;%PATH%"
if not defined JAVA_HOME echo Note: JAVA_HOME is not set. Running project builds may need a JDK.

set "TARGET=%~1"
if "%TARGET%"=="" (
    set "TARGET=%USERPROFILE%\codedna-demo"
    if not exist "%USERPROFILE%\codedna-demo" (
        echo Creating the demo project in %USERPROFILE%\codedna-demo ...
        call ".venv\Scripts\python" scripts\make_demo_repo.py "%USERPROFILE%\codedna-demo" || exit /b 1
    )
)

rem Last commit that changed the IDE; after a pull that changes it, rebuild.
rem Without git on PATH the IDE is only built when it has never been built.
set "IDE_REV="
for /f "usebackq delims=" %%r in (`git log -1 "--format=%%H" -- ide 2^>nul`) do set "IDE_REV=%%r"

cd ide
if not exist "node_modules" (
    echo Installing the IDE, first run only ...
    call npm install || exit /b 1
)
set "STAMP=electron-app\lib\codedna-build.txt"
set "BUILT_REV="
if exist "%STAMP%" set /p BUILT_REV=<"%STAMP%"
if not exist "electron-app\lib\backend\main.js" goto build
if defined IDE_REV if not "%IDE_REV%"=="%BUILT_REV%" goto build
goto built
:build
echo Building the IDE (first run, or the IDE code changed) ...
call npm run build || exit /b 1
if defined IDE_REV >"%STAMP%" echo %IDE_REV%
:built

echo Starting the CodeDNA IDE on %TARGET%
echo Keep this window open while you use the IDE; closing it closes the IDE.
cd electron-app
call "..\node_modules\.bin\theia.cmd" start "%TARGET%"

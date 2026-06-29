@echo off
for /f "tokens=*" %%i in ('where git') do (
    if not "%%i"=="%~dp0git.cmd" (
        set "REAL_GIT=%%i"
        goto :run
    )
)

:run
if "%1"=="diff" (
    "%REAL_GIT%" %* | python "%~dp0..\uc" rtk-filter git-diff
) else if "%1"=="status" (
    "%REAL_GIT%" %* | python "%~dp0..\uc" rtk-filter git-status
) else (
    "%REAL_GIT%" %*
)

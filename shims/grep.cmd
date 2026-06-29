@echo off
for /f "tokens=*" %%i in ('where grep') do (
    if not "%%i"=="%~dp0grep.cmd" (
        set "REAL_GREP=%%i"
        goto :run
    )
)

:run
"%REAL_GREP%" %* | python "%~dp0..\uc" rtk-filter grep

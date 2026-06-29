@echo off
for /f "tokens=*" %%i in ('where rg') do (
    if not "%%i"=="%~dp0rg.cmd" (
        set "REAL_RG=%%i"
        goto :run
    )
)

:run
"%REAL_RG%" %* | python "%~dp0..\uc" rtk-filter rg

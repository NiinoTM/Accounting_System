@echo off
REM Start the Nuitka build process for the application
echo Starting Nuitka build process...

python -m nuitka --standalone --windows-disable-console --windows-icon-from-ico="C:\Users\Niino\Desktop\Accounting_System\data\base.ico" --include-data-dir=data=data --follow-imports --enable-plugin=pyside6 main.py

echo Build process complete.
pause

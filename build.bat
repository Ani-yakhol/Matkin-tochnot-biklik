@echo off
chcp 65001 >nul
echo ================================================
echo  מתקין תוכנות בקליק v5.4 - קמפול לקובץ EXE
echo ================================================
echo.
echo בחר סוג קמפול:
echo   [1] תיקיית הפצה (כמה קבצים, הרצה מהירה יותר) - מומלץ
echo   [2] קובץ EXE יחיד (קובץ אחד, הרצה איטית יותר בפתיחה)
echo.
set /p BUILD_MODE="הקלד 1 או 2 ואז Enter: "

REM בדיקת Python
python --version >nul 2>&1
if errorlevel 1 (
    echo שגיאה: Python לא מותקן או לא נמצא ב-PATH
    echo הורד Python מ: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] מתקין תלויות...
pip install -r requirements.txt --upgrade -q
if errorlevel 1 (
    echo שגיאה בהתקנת תלויות
    pause
    exit /b 1
)

set ICON_ARG=
if exist "app_icon.ico" (
    set ICON_ARG=--icon=app_icon.ico
    echo נמצא קובץ אייקון: app_icon.ico
) else (
    echo אזהרה: לא נמצא app_icon.ico - הקובץ יקומפל ללא אייקון מותאם ל-EXE
)

echo [2/3] מקמפל...

if "%BUILD_MODE%"=="2" (
    pyinstaller main.py --name SoftInstaller --onefile --windowed %ICON_ARG% --uac-admin --noconfirm --clean
) else (
    pyinstaller main.py --name SoftInstaller --windowed %ICON_ARG% --uac-admin --noconfirm --clean
)

if errorlevel 1 (
    echo שגיאה בקמפול
    pause
    exit /b 1
)

echo [3/3] מסדר תיקיות...

if "%BUILD_MODE%"=="2" (
    if not exist "dist\software" mkdir "dist\software"
    if not exist "dist\icons" mkdir "dist\icons"
    if not exist "dist\reports" mkdir "dist\reports"
    if exist "icons\*" xcopy /Y /Q /E "icons\*" "dist\icons\" >nul
    echo.
    echo ================================================
    echo  הצלחה! הקובץ נמצא בתיקייה: dist\
    echo  SoftInstaller.exe הוא קובץ עצמאי יחיד
    echo  העתק את כל תיקיית dist\ (כולל software, icons, reports)
    echo ================================================
) else (
    if not exist "dist\SoftInstaller\software" mkdir "dist\SoftInstaller\software"
    if not exist "dist\SoftInstaller\icons" mkdir "dist\SoftInstaller\icons"
    if not exist "dist\SoftInstaller\reports" mkdir "dist\SoftInstaller\reports"
    if exist "icons\*" xcopy /Y /Q /E "icons\*" "dist\SoftInstaller\icons\" >nul
    echo.
    echo ================================================
    echo  הצלחה! הקובץ נמצא בתיקייה: dist\
    echo  העתק את תיקיית dist\SoftInstaller כולה
    echo  (כולל תיקיות software, icons, reports)
    echo ================================================
)

echo.
pause

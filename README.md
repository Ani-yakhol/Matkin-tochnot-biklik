# 🛠️ מדריך מפתח — מתקין תוכנות בקליק v5.4

מדריך זה מיועד למפתח/מתחזק הכלי. הוא מסביר כיצד להקים סביבת עבודה, להריץ את הכלי ישירות מקוד המקור, ולקמפל אותו לקובץ EXE עצמאי בשני אופנים.

---

## 1. דרישות מערכת

| רכיב | גרסה נדרשת |
|---|---|
| מערכת הפעלה | Windows 10 / 11 (64-bit מומלץ) |
| Python | 3.8 ומעלה (מומלץ 3.10+) |
| הרשאות | Administrator — נדרש לזיהוי תוכנות מותקנות, יצירת קיצורי דרך, והתקנות בפועל |

ספריות Python נדרשות (ראו `requirements.txt`):

```
PyQt5>=5.15.0
pywin32>=305
pyinstaller>=5.0
winshell>=0.6
```

- **PyQt5** — ממשק המשתמש הגרפי (GUI)
- **pywin32** — גישה ל-COM של Windows (`win32com.client`) ליצירת קיצורי דרך (`.lnk`)
- **winshell** — איתור נתיבי שולחן עבודה (פרטי/ציבורי)
- **pyinstaller** — קמפול ל-EXE עצמאי

---

## 2. התקנת הסביבה

### בדיקת Python מותקן
```cmd
python --version
```
אם הפקודה לא מזוהה — התקן Python מ-https://www.python.org/downloads/ (סמן "Add Python to PATH" בזמן ההתקנה).

### התקנת ספריות בודדות (CMD)
```cmd
pip install PyQt5 pywin32 pyinstaller winshell
```

### התקנה מתוך requirements.txt (מומלץ)
```cmd
pip install -r requirements.txt
```

### עדכון ספריות קיימות לגרסה האחרונה
```cmd
pip install -r requirements.txt --upgrade
```

---

## 3. הרצה ישירה לבדיקות (ללא קמפול)

```cmd
python main.py
```

> **חשוב:** חלק נכבד מהפיצ'רים — זיהוי תוכנות מותקנות מהרג'יסטרי, יצירת/איתור קיצורי דרך, והתקנות בפועל — דורשים **הרצה כ-Administrator**. פתח את שורת הפקודה (CMD) במצב "הפעל כמנהל" (Run as Administrator) לפני ביצוע הפקודה לעיל.

---

## 4. מבנה הפרויקט וקבצי נתונים בזמן ריצה

```
SoftInstaller/
├── main.py                    ← קוד המקור הראשי (v5.4)
├── requirements.txt           ← רשימת תלויות Python
├── build.bat                  ← סקריפט קמפול (תיקיית הפצה / קובץ יחיד)
├── app_icon.ico                ← אייקון הכלי לשימוש בקמפול (EXE/שורת משימות)
├── icons/                      ← אייקוני תוכנות בודדות + גרסאות PNG של אייקון הכלי
├── SoftInstaller_Setup.iss     ← סקריפט Inno Setup (מתקין בעברית מלאה)
├── DEV_GUIDE.md                 ← מדריך זה
├── software/                    ← קבצי התקנה (.exe/.msi) — נוצר אוטומטית, וכן מכיל את config.json
│   └── config.json              ← קובץ ההגדרות בפועל (קטגוריות, תוכנות, סיסמאות מוצפנות)
├── icons/                       ← אייקוני תוכנות שנשמרו דרך הממשק
├── reports/                     ← דו"חות מיוצאים (HTML/TXT)
└── .session.json                ← session זמני להמשך התקנה לאחר כיבוי (נמחק בסיום)
```

**הערה חשובה על מיקום config.json:** הכלי שומר את קובץ ההגדרות בתוך `software\config.json` כברירת מחדל (כך שניתן להעתיק את כל ה-USB בקלות). אם כבר קיים `config.json` ישירות בתיקיית הבסיס (תאימות לאחור מגרסאות קודמות) — הכלי ימשיך להשתמש בו שם.

---

## 5. קמפול לקובץ EXE

ניתן לקמפל בשני אופנים — תיקיית הפצה (מומלץ) או קובץ יחיד. `build.bat` תומך בשני המצבים.

### מצב 1 — תיקיית הפצה (Directory Bundle) — מומלץ
- יוצר תיקייה `dist\SoftInstaller\` עם `SoftInstaller.exe` וכל קבצי ה-DLL בנפרד.
- **יתרון:** זמן פתיחה מהיר משמעותית.
- **חיסרון:** הפצה דורשת העתקת תיקייה שלמה, לא קובץ בודד.
- מתאים במיוחד לעבודה ארוכת טווח מ-USB/און-קי.

### מצב 2 — קובץ EXE יחיד (Onefile)
- יוצר קובץ `dist\SoftInstaller.exe` בודד.
- **יתרון:** קובץ אחד נוח להעברה/הפצה/מייל.
- **חיסרון:** בכל הפעלה הקובץ מחלץ את עצמו לתיקייה זמנית — פתיחה איטית יותר (כמה שניות נוספות).

### הרצת build.bat
```cmd
build.bat
```
הסקריפט ישאל אותך לבחור מצב קמפול (1 או 2), יתקין תלויות במידת הצורך, ויקמפל בהתאם.

הקובץ המוכן יימצא תחת `dist\`. **חובה להעתיק יחד עם הקובץ גם את התיקיות** `software\`, `icons\`, `reports\` הנוצרות אוטומטית.

---

## 6. קמפול ידני (ללא build.bat) — לעיון מתקדם

### מצב תיקיית הפצה:
```cmd
pyinstaller main.py --name SoftInstaller --windowed --icon=app_icon.ico --uac-admin --noconfirm
```

### מצב קובץ יחיד:
```cmd
pyinstaller main.py --name SoftInstaller --onefile --windowed --icon=app_icon.ico --uac-admin --noconfirm
```

הסבר הדגלים:
- `--windowed` — ללא חלון קונסולה (GUI בלבד, כפי שהכלי בנוי)
- `--icon=app_icon.ico` — מטמיע את אייקון הכלי בקובץ ה-EXE (לשורת המשימות וסייר הקבצים)
- `--uac-admin` — מבקש הרשאות מנהל אוטומטית בהפעלה (חיוני לזיהוי תוכנות והתקנות)
- `--onefile` — קובץ יחיד (השמט לקבלת תיקיית הפצה)
- `--noconfirm` — דורס פלט קודם ללא שאלות אישור

> שימו לב: אייקון האפליקציה (החלון, הספלאש) כבר מוטמע בקוד עצמו כ-Base64 ואינו תלוי בקובץ `app_icon.ico` החיצוני. קובץ ה-ICO החיצוני נדרש רק כדי להטביע אייקון בקובץ ה-**EXE עצמו** (מה שמוצג בסייר הקבצים ובשורת המשימות לפני הרצת התוכנה).

---

## 7. בעיות נפוצות בקמפול

| בעיה | פתרון |
|---|---|
| `ModuleNotFoundError: winshell` | ודא ש-`pip install winshell` רץ בהצלחה לפני הקמפול |
| הכלי לא מזהה תוכנות מותקנות / לא יוצר קיצורי דרך | ודא הרצה כ-Administrator |
| אייקון לא מופיע בקובץ ה-EXE | ודא ש-`app_icon.ico` נמצא באותה תיקייה כמו `main.py` בזמן הקמפול |
| אנטי-וירוס חוסם את ה-EXE | תופעה נפוצה עם PyInstaller — הוסף חריג (False Positive) או חתום דיגיטלית את הקובץ |
| שגיאת קידוד עברית בקונסולה | אין צורך לדאוג — הכלי רץ במצב `--windowed` ללא קונסולה |

---

## 8. אריזת מתקין (Installer) עם Inno Setup

לאחר קמפול מוצלח, ניתן לארוז את הכלי במתקין מקצועי עם ממשק עברי מלא. ראו את הקובץ `SoftInstaller_Setup.iss` ואת ההוראות המפורטות בתוכו.

בקצרה:
1. התקן [Inno Setup](https://jrsoftware.org/isinfo.php)
2. הורד את `Hebrew.isl` מ-https://jrsoftware.org/files/istrans/ והנח בתיקיית `Languages` של Inno Setup (לרוב: `C:\Program Files (x86)\Inno Setup 6\Languages\Hebrew.isl`)
3. פתח את `SoftInstaller_Setup.iss` ב-Inno Setup Compiler
4. ודא שהנתיבים בסעיף `[Files]` תואמים למצב הקמפול שבחרת (תיקיית הפצה / קובץ יחיד) — ראה הערות בתוך הקובץ
5. הרץ Build (F9) — הפלט יהיה ב-`installer_output\SoftInstaller_Setup_v5.4.exe`

---

## 9. עדכון גרסה עתידי

בעת עדכון גרסה, יש לעדכן את המספר במקומות הבאים בתוך `main.py`:
- שורת הדוקסטרינג בראש הקובץ (`v5.4`)
- המשתנה `APP_VER="5.4"`
- שני מילוני `about_text` בתוך `TRANSLATIONS` (עברית ואנגלית)

וכן:
- `SoftInstaller_Setup.iss` — `#define MyAppVersion "5.4"`
- `README.md` — כותרת ראשית (אם קיים)

---

*מדריך זה מתעדכן בהתאם לגרסת הכלי. גרסה נוכחית: 5.4*


# תמונות

<img width="998" height="789" alt="מתקין תוכנות בקליק 1" src="https://github.com/user-attachments/assets/50185729-4d3d-4ddf-be56-842d12c1e6a3" />
<img width="957" height="748" alt="מתקין תוכנות בקליק 2" src="https://github.com/user-attachments/assets/ed86e81d-8e14-462a-8d2a-ffc962203cd7" />

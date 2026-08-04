#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
מתקין תוכנות בקליק - One-Click Software Installer  v5.4
"""
import sys, os
BASE_DIR     = os.path.dirname(os.path.abspath(sys.argv[0]))
SOFTWARE_DIR = os.path.join(BASE_DIR,"software")
ICONS_DIR    = os.path.join(BASE_DIR,"icons")
REPORTS_DIR  = os.path.join(BASE_DIR,"reports")
SESSION_FILE = os.path.join(BASE_DIR,".session.json")
# config.json: ברירת מחדל בתיקיית software (נתיב יחסי)
_DEFAULT_CONFIG = os.path.join(SOFTWARE_DIR,"config.json")
# אם קיים config.json בתיקיית BASE_DIR (תאימות לאחור) — השתמש בו
CONFIG_FILE = _DEFAULT_CONFIG if not os.path.exists(os.path.join(BASE_DIR,"config.json")) else os.path.join(BASE_DIR,"config.json")
for _d in [SOFTWARE_DIR,ICONS_DIR,REPORTS_DIR]: os.makedirs(_d,exist_ok=True)

from PyQt5.QtWidgets import *
from PyQt5.QtCore    import *
from PyQt5.QtGui     import *
import json,hashlib,subprocess,winreg,shutil,datetime,winsound,threading,base64,glob

APP_NAME="מתקין תוכנות בקליק"; APP_VER="5.4"

# ─── תרגום כפתורי QMessageBox ───
def _translate_buttons(msgbox, lang):
    """מתרגם כפתורי Yes/No/Ok/Cancel לפי שפה"""
    btn_map_he = {
        QMessageBox.Yes: "כן", QMessageBox.No: "לא",
        QMessageBox.Ok: "אישור", QMessageBox.Cancel: "ביטול",
        QMessageBox.Close: "סגור", QMessageBox.Apply: "החל",
    }
    btn_map_en = {
        QMessageBox.Yes: "Yes", QMessageBox.No: "No",
        QMessageBox.Ok: "OK", QMessageBox.Cancel: "Cancel",
        QMessageBox.Close: "Close", QMessageBox.Apply: "Apply",
    }
    mapping = btn_map_he if lang == "he" else btn_map_en
    for btn_role, text in mapping.items():
        btn = msgbox.button(btn_role)
        if btn: btn.setText(text)

def show_question(parent, title, text, buttons=QMessageBox.Yes|QMessageBox.No):
    """QMessageBox.question עם כפתורים מתורגמים"""
    lang = CONFIG.data.get("language","he")
    mb = QMessageBox(parent)
    mb.setWindowTitle(title); mb.setText(text)
    mb.setStandardButtons(buttons)
    mb.setLayoutDirection(Qt.RightToLeft if lang=="he" else Qt.LeftToRight)
    _translate_buttons(mb, lang)
    return mb.exec_()

def show_info(parent, title, text):
    lang = CONFIG.data.get("language","he")
    mb = QMessageBox(parent)
    mb.setWindowTitle(title); mb.setText(text)
    mb.setStandardButtons(QMessageBox.Ok)
    mb.setLayoutDirection(Qt.RightToLeft if lang=="he" else Qt.LeftToRight)
    _translate_buttons(mb, lang)
    mb.exec_()

def show_warning(parent, title, text):
    lang = CONFIG.data.get("language","he")
    mb = QMessageBox(parent)
    mb.setWindowTitle(title); mb.setText(text); mb.setIcon(QMessageBox.Warning)
    mb.setStandardButtons(QMessageBox.Ok)
    mb.setLayoutDirection(Qt.RightToLeft if lang=="he" else Qt.LeftToRight)
    _translate_buttons(mb, lang)
    mb.exec_()

def show_critical(parent, title, text):
    lang = CONFIG.data.get("language","he")
    mb = QMessageBox(parent)
    mb.setWindowTitle(title); mb.setText(text); mb.setIcon(QMessageBox.Critical)
    mb.setStandardButtons(QMessageBox.Ok)
    mb.setLayoutDirection(Qt.RightToLeft if lang=="he" else Qt.LeftToRight)
    _translate_buttons(mb, lang)
    mb.exec_()

# ══════════════ תרגומים ══════════════
TRANSLATIONS={
"he":{
  "app_name":"מתקין תוכנות בקליק",
  "settings":"⚙️ הגדרות","scan":"🔍 סרוק תוכנות","refresh":"🔄 רענן",
  "search_ph":"🔍 חפש תוכנה...",
  "expand_all":"▼ הרחב הכל","collapse_all":"▶ כווץ הכל",
  "expand_desc":"📄 הרחב תיאור","collapse_desc":"📄 כווץ תיאור",
  "select_all":"☑ סמן הכל","clear_all":"☐ נקה הכל",
  "install_selected":"🚀 התקן נבחרים","last_report":"📄 דו\"ח אחרון",
  "silent_install":"🔇 שקטה","normal_install":"🖥️ רגילה",
  "notify_on_done":"🔔 הודעה וצליל בסיום","ready":"מוכן להתקנה",
  "tab_categories":"📂 קטגוריות","tab_sw":"💿 תוכנות",
  "tab_silent":"🔇 התקנה שקטה","tab_security":"🔒 אבטחה",
  "tab_general":"⚙️ כללי","tab_about":"ℹ️ אודות",
  "tab_io":"📤 ייצוא/ייבוא","tab_settings":"הגדרות",
  "save_close":"💾 שמור וסגור",
  "no_software":"אין תוכנות ברשימה.\nהוסף תוכנות דרך ⚙️ הגדרות.",
  "install_btn":"▶ התקן","installed_mark":"✅ מותקן",
  "installing":"⏳ מתקין...","done":"✅ הותקן",
  "error":"❌ שגיאה","skipped":"⏭️ דולג","manual":"👤 ידני",
  "language":"שפה / Language","report_title":"דו\"ח התקנה",
  "about_text":(
    "<h2>מתקין תוכנות בקליק</h2><p style='color:#666;'>גרסה 5.4</p><hr>"
    "<p>התוכנה נבנתה בכדי להקל על התקנת תוכנות במחשבים חדשים.<br>"
    "מאפשרת התקנה אוטומטית שקטה של מספר תוכנות בלחיצה אחת,<br>"
    "ומיועדת לשימוש נייד מ-USB ואון-קי — ללא צורך בהתקנה.</p>"
    "<p><b>תכונות עיקריות:</b></p>"
    "<ul><li>התקנה שקטה אוטומטית</li>"
    "<li>ניהול קטגוריות, תגיות וחיפוש</li>"
    "<li>זיהוי אוטומטי של סוג המתקין</li>"
    "<li>פעולות לאחר התקנה</li>"
    "<li>המשך התקנה לאחר כיבוי</li>"
    "<li>עבודה נייד מ-USB ללא התקנה</li></ul>"
  ),
},
"en":{
  "app_name":"One-Click Software Installer",
  "settings":"⚙️ Settings","scan":"🔍 Scan Installed","refresh":"🔄 Refresh",
  "search_ph":"🔍 Search software...",
  "expand_all":"▼ Expand All","collapse_all":"▶ Collapse All",
  "expand_desc":"📄 Expand Description","collapse_desc":"📄 Collapse Description",
  "select_all":"☑ Select All","clear_all":"☐ Clear All",
  "install_selected":"🚀 Install Selected","last_report":"📄 Last Report",
  "silent_install":"🔇 Silent","normal_install":"🖥️ Normal",
  "notify_on_done":"🔔 Notify on complete","ready":"Ready to install",
  "tab_categories":"📂 Categories","tab_sw":"💿 Software",
  "tab_silent":"🔇 Silent Install","tab_security":"🔒 Security",
  "tab_general":"⚙️ General","tab_about":"ℹ️ About",
  "tab_io":"📤 Export/Import","tab_settings":"Settings",
  "save_close":"💾 Save & Close",
  "no_software":"No software in list.\nAdd software via ⚙️ Settings.",
  "install_btn":"▶ Install","installed_mark":"✅ Installed",
  "installing":"⏳ Installing...","done":"✅ Installed",
  "error":"❌ Error","skipped":"⏭️ Skipped","manual":"👤 Manual",
  "language":"Language / שפה","report_title":"Installation Report",
  "about_text":(
    "<h2>One-Click Software Installer</h2><p style='color:#666;'>Version 5.4</p><hr>"
    "<p>Built to simplify software installation on new computers.<br>"
    "Enables silent automatic installation of multiple programs in one click,<br>"
    "designed for portable use from USB drives — no installation needed.</p>"
    "<p><b>Key Features:</b></p>"
    "<ul><li>Automatic silent installation</li>"
    "<li>Categories, tags and search</li>"
    "<li>Auto-detection of installer type</li>"
    "<li>Post-install actions</li>"
    "<li>Resume after shutdown</li>"
    "<li>Portable USB operation</li></ul>"
  ),
},
}

# ══════════════ ConfigManager ══════════════
class ConfigManager:
    DEFAULT={
        "tool_password":"","settings_password":"",
        "categories":[],"software":[],
        "notify_on_complete":True,"sound_on_complete":True,
        "language":"he",
        "custom_silent_types":[],
    }
    def __init__(self):
        self.data={}
        self._config_file=CONFIG_FILE
        self.load()

    def get_config_path(self): return self._config_file

    def set_config_path(self, path):
        """שינוי נתיב קובץ ה-config + טעינה מחדש"""
        global CONFIG_FILE
        self._config_file=path
        CONFIG_FILE=path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self.load()

    def load(self):
        cf=self._config_file if hasattr(self,"_config_file") else CONFIG_FILE
        if os.path.exists(cf):
            try:
                with open(cf,"r",encoding="utf-8") as f: self.data=json.load(f)
            except: self.data=dict(self.DEFAULT)
        else: self.data=dict(self.DEFAULT)
        for k,v in self.DEFAULT.items():
            if k not in self.data: self.data[k]=v

    def save(self):
        cf=self._config_file if hasattr(self,"_config_file") else CONFIG_FILE
        os.makedirs(os.path.dirname(cf) or ".", exist_ok=True)
        with open(cf,"w",encoding="utf-8") as f: json.dump(self.data,f,ensure_ascii=False,indent=2)
    def hash_password(self,pw): return hashlib.sha256(pw.encode()).hexdigest() if pw else ""
    def check_password(self,key,pw):
        s=self.data.get(key,""); return (not s) or s==self.hash_password(pw)
    def set_password(self,key,pw): self.data[key]=self.hash_password(pw); self.save()
    def clear_password(self,key): self.data[key]=""; self.save()
    def resolve_file(self,filepath):
        """יחסי -> מוחלט: מחפש בתיקיית software ובתת-תיקיות"""
        if not filepath: return ""
        if os.path.isabs(filepath): return filepath
        cand=os.path.join(SOFTWARE_DIR,filepath)
        if os.path.exists(cand): return cand
        fname=os.path.basename(filepath)
        for root,_,files in os.walk(SOFTWARE_DIR):
            if fname in files: return os.path.join(root,fname)
        return filepath
    def make_relative(self,filepath,force_absolute=False):
        """מוחלט -> יחסי אם force_absolute=False"""
        if force_absolute or not filepath: return filepath
        try:
            rel=os.path.relpath(filepath,SOFTWARE_DIR)
            if not rel.startswith(".."): return rel
        except ValueError: pass
        return filepath

CONFIG=ConfigManager()

def TR(key):
    lang=CONFIG.data.get("language","he")
    return TRANSLATIONS.get(lang,TRANSLATIONS["he"]).get(key,key)
def get_dir():
    return Qt.RightToLeft if CONFIG.data.get("language","he")=="he" else Qt.LeftToRight

# ══════════════ Silent presets ══════════════
BASE_SILENT_PRESETS={
    "NSIS":"/S",
    "Inno Setup":"/VERYSILENT /SUPPRESSMSGBOXES /NORESTART",
    "MSI":"/qn /norestart",
    "InstallShield":'/s /v"/qn"',
    "Squirrel":"--silent",
    "7-Zip SFX":"/S",
    "WiX":"/qn",
    "ללא ארגומנטים":"",
    "מותאם אישית":"",
}
def get_all_presets():
    p=dict(BASE_SILENT_PRESETS)
    for ct in CONFIG.data.get("custom_silent_types",[]):
        p[ct["name"]]=ct["args"]
    return p

# ══════════════ helper functions ══════════════
def get_arch_label():
    """מזהה ארכיטקטורת המחשב ומחזיר תווית עברית"""
    import platform, struct
    machine = platform.machine().upper()
    bits = struct.calcsize("P") * 8
    # בדיקה מדויקת דרך winreg
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment")
        proc_arch = winreg.QueryValueEx(key, "PROCESSOR_ARCHITECTURE")[0]
        key.Close()
        if proc_arch.upper() in ("AMD64", "EM64T", "X86_64", "ARM64", "AARCH64"):
            return "מחשב זוהה: 64 סביות"
        elif proc_arch.upper() in ("X86",):
            return "מחשב זוהה: 32 סביות"
    except:
        pass
    if bits == 64 or machine in ("AMD64","X86_64","AARCH64","ARM64"):
        return "מחשב זוהה: 64 סביות"
    return "מחשב זוהה: 32 סביות"

ARCH_LABEL = get_arch_label()

def parse_tech_item(raw: str) -> str:
    """
    ממיר פרט טכני לטקסט עם סמל:
    אנגלית:  V xxx → ✅ xxx | X xxx → ❌ xxx | ? xxx → ❓ xxx
    עברית:   וי xxx → ✅ xxx | איקס xxx → ❌ xxx | שאלה xxx → ❓ xxx
    """
    s = raw.strip()
    low = s.lower()
    # עברית
    if low.startswith("וי "):       return f"✅ {s[3:].strip()}"
    if low.startswith("איקס "):     return f"❌ {s[5:].strip()}"
    if low.startswith("שאלה "):     return f"❓ {s[5:].strip()}"
    # אנגלית
    if s.upper().startswith("V "):  return f"✅ {s[2:].strip()}"
    if s.upper().startswith("X "):  return f"❌ {s[2:].strip()}"
    if s.startswith("? "):          return f"❓ {s[2:].strip()}"
    return f"• {s}"

def parse_tech_html(raw: str) -> str:
    """ממיר מחרוזת פרטים טכניים ל-HTML עם סמלים צבעוניים"""
    items = [t.strip() for t in raw.split(",") if t.strip()]
    parts = []
    for it in items:
        text = parse_tech_item(it)
        if text.startswith("✅"):
            parts.append(f"<span style='color:#27ae60;font-weight:bold;'>{text}</span>")
        elif text.startswith("❌"):
            parts.append(f"<span style='color:#e74c3c;font-weight:bold;'>{text}</span>")
        elif text.startswith("❓"):
            # סמל שאלה — כחול
            parts.append(f"<span style='color:#2980b9;font-weight:bold;'>{text}</span>")
        else:
            parts.append(f"<span style='color:#555;'>{text}</span>")
    return "&nbsp;&nbsp;".join(parts)

def extract_icon_from_exe(exe_path,out_dir=None):
    if out_dir is None: out_dir=ICONS_DIR
    try:
        provider=QFileIconProvider(); qicon=provider.icon(QFileInfo(exe_path))
        if not qicon.isNull():
            out=os.path.join(out_dir,os.path.splitext(os.path.basename(exe_path))[0]+"_icon.png")
            pix=qicon.pixmap(48,48)
            if not pix.isNull(): pix.save(out,"PNG"); return os.path.basename(out)  # שמור רק שם קובץ — תאימות USB
    except: pass
    return ""

def detect_silent_type(filepath):
    if os.path.basename(filepath).lower().endswith(".msi"): return "MSI","/qn /norestart"
    try:
        with open(filepath,"rb") as f: h=f.read(32768).lower()
        if b"nullsoft" in h or b"nsis" in h: return "NSIS","/S"
        if b"inno" in h: return "Inno Setup","/VERYSILENT /SUPPRESSMSGBOXES /NORESTART"
        if b"installshield" in h: return "InstallShield",'/s /v"/qn"'
        if b"squirrel" in h: return "Squirrel","--silent"
        if b"wix" in h or b"windows installer" in h: return "WiX","/qn"
        if b"7-zip" in h or b"sfx" in h: return "7-Zip SFX","/S"
        if b"burn" in h or b"bootstrapper" in h: return "WiX","/quiet"
    except: pass
    return "מותאם אישית",""

# ══════════════ Icon helpers (USB/portable path handling) ══════════════
def resolve_icon(icon_path):
    """מחזיר נתיב מוחלט לאייקון — תומך בנתיב יחסי לתיקיית icons"""
    if not icon_path: return ""
    if os.path.isabs(icon_path) and os.path.exists(icon_path): return icon_path
    # נסה יחסי לתיקיית icons (נתיב יחסי או שם קובץ בלבד)
    cand = os.path.join(ICONS_DIR, icon_path)
    if os.path.exists(cand): return cand
    # נסה שם קובץ בלבד
    fname = os.path.basename(icon_path)
    if fname:
        cand2 = os.path.join(ICONS_DIR, fname)
        if os.path.exists(cand2): return cand2
    return ""

def make_icon_relative(icon_path):
    """הופך נתיב אייקון ליחסי (שם קובץ בלבד) — לתאימות USB"""
    if not icon_path: return ""
    # אם הקובץ בתיקיית icons — שמור רק שם הקובץ
    try:
        rel = os.path.relpath(icon_path, ICONS_DIR)
        if not rel.startswith(".."):
            return os.path.basename(icon_path)
    except ValueError: pass
    # אם הקובץ מחוץ לתיקייה — שמור שם קובץ בלבד
    return os.path.basename(icon_path)

def find_installed_exe(sw_name):
    """מחפש את ה-EXE של תוכנה מותקנת ב-Registry"""
    reg_paths=[
        (winreg.HKEY_LOCAL_MACHINE,r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE,r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]
    nl=sw_name.lower()
    for hive,path in reg_paths:
        try:
            key=winreg.OpenKey(hive,path)
            for i in range(winreg.QueryInfoKey(key)[0]):
                try:
                    sk=winreg.OpenKey(key,winreg.EnumKey(key,i))
                    try:
                        dn=winreg.QueryValueEx(sk,"DisplayName")[0]
                        if nl in dn.lower() or dn.lower() in nl:
                            icon=loc=""
                            try: icon=winreg.QueryValueEx(sk,"DisplayIcon")[0]
                            except: pass
                            try: loc=winreg.QueryValueEx(sk,"InstallLocation")[0]
                            except: pass
                            cand=icon.split(",")[0].strip('"').strip() if icon else ""
                            if cand and os.path.isfile(cand): return cand
                            if loc:
                                for root,_,files in os.walk(loc):
                                    for f2 in files:
                                        if f2.lower().endswith(".exe") and dn.split()[0].lower() in f2.lower():
                                            return os.path.join(root,f2)
                    except: pass
                    sk.Close()
                except: pass
            key.Close()
        except: pass
    return ""

def find_desktop_shortcut(sw_name):
    """מחפש קיצור דרך (.lnk) קיים בשולחן העבודה (פרטי/ציבורי) לפי שם תוכנה"""
    desktops=[]
    try:
        import winshell
        desktops.append(winshell.desktop())
        try: desktops.append(winshell.common_desktop())
        except: pass
    except: pass
    desktops.append(os.path.join(os.environ.get("USERPROFILE",""), "Desktop"))
    desktops.append(os.path.join(os.environ.get("PUBLIC","C:\\Users\\Public"), "Desktop"))
    nl=sw_name.lower()
    seen=set()
    for dpath in desktops:
        if not dpath or dpath in seen or not os.path.isdir(dpath): continue
        seen.add(dpath)
        try:
            for fn in os.listdir(dpath):
                if fn.lower().endswith(".lnk"):
                    base=os.path.splitext(fn)[0].lower()
                    if nl in base or base in nl:
                        return os.path.join(dpath, fn)
        except: pass
    return ""

SYS_KW=["Microsoft Visual C++","Microsoft .NET","Windows SDK","Update for Windows",
         "Security Update","Hotfix","KB","Redistributable","Runtime","Driver",
         "DirectX","Windows Desktop Runtime","Microsoft Edge Update",
         "Microsoft Update Health","Windows Malicious"]
CAT_KW={
    "גרפיקה ועיצוב":["photoshop","illustrator","gimp","inkscape","paint","canva","figma","coreldraw","lightroom","affinity","sketchup"],
    "וידאו":["premiere","vegas","resolve","camtasia","kdenlive","handbrake","vlc","obs"],
    "אודיו":["audacity","reaper","foobar","winamp","spotify","itunes","audition","fl studio"],
    "פיתוח":["visual studio","vscode","git","python","node","java","eclipse","intellij","android studio","notepad++","sublime"],
    "משרד":["office","word","excel","powerpoint","libreoffice","openoffice","acrobat","pdf","outlook"],
    "דפדפן":["chrome","firefox","edge","opera","brave","safari","tor browser"],
    "אבטחה":["antivirus","malwarebytes","kaspersky","avast","avg","bitdefender","norton","eset"],
    "כלי מערכת":["ccleaner","7-zip","winrar","defraggler","cpu-z","hwinfo","aida","sysinternals"],
    "תקשורת":["zoom","teams","skype","slack","discord","telegram","whatsapp","signal","viber"],
    "משחקים":["steam","epic","game","uplay","origin","battle.net","gog"],
    "כלל":[],
}
def guess_category(name,publisher=""):
    t=(name+" "+publisher).lower()
    for cat,kws in CAT_KW.items():
        if kws and any(kw in t for kw in kws): return cat
    return "כלל"

def get_installed_software():
    reg_paths=[
        (winreg.HKEY_LOCAL_MACHINE,r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE,r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]
    seen,result=set(),[]
    for hive,path in reg_paths:
        try:
            key=winreg.OpenKey(hive,path)
            for i in range(winreg.QueryInfoKey(key)[0]):
                try:
                    sk=winreg.OpenKey(key,winreg.EnumKey(key,i))
                    try:
                        name=winreg.QueryValueEx(sk,"DisplayName")[0]
                        pub=ver=dt=icon=""
                        try: pub=winreg.QueryValueEx(sk,"Publisher")[0]
                        except: pass
                        try: ver=winreg.QueryValueEx(sk,"DisplayVersion")[0]
                        except: pass
                        try: dt=winreg.QueryValueEx(sk,"InstallDate")[0]
                        except: pass
                        try: icon=winreg.QueryValueEx(sk,"DisplayIcon")[0]
                        except: pass
                        sc=0
                        try: sc=winreg.QueryValueEx(sk,"SystemComponent")[0]
                        except: pass
                        is_sys=any(kw.lower() in name.lower() for kw in SYS_KW)
                        if name and not is_sys and sc==0 and name not in seen:
                            seen.add(name)
                            result.append({"name":name,"publisher":pub,"version":ver,
                                           "install_date":dt,"icon":icon,
                                           "category":guess_category(name,pub)})
                    except: pass
                    sk.Close()
                except: pass
            key.Close()
        except: pass
    return sorted(result,key=lambda x:x["name"].lower())


# ══════════════ Session (resume after shutdown) ══════════════
def save_session(remaining_sw,done_report):
    try:
        data={"remaining":[s["id"] for s in remaining_sw],"done":done_report,
              "timestamp":datetime.datetime.now().isoformat()}
        with open(SESSION_FILE,"w",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False,indent=2)
    except: pass

def load_session():
    if not os.path.exists(SESSION_FILE): return None
    try:
        with open(SESSION_FILE,"r",encoding="utf-8") as f: return json.load(f)
    except: return None

def clear_session():
    try: os.remove(SESSION_FILE)
    except: pass

# ══════════════ Splash screen SVG icon ══════════════
SPLASH_SVG = (
    b'<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300" viewBox="0 0 300 300">'
    b'<defs><linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">'
    b'<stop offset="0%" style="stop-color:#1a2a4a"/>'
    b'<stop offset="100%" style="stop-color:#0d6b3c"/></linearGradient>'
    b'<linearGradient id="ar" x1="0%" y1="0%" x2="100%" y2="0%">'
    b'<stop offset="0%" style="stop-color:#2ecc71"/>'
    b'<stop offset="100%" style="stop-color:#27ae60"/></linearGradient></defs>'
    b'<rect width="300" height="300" rx="40" fill="url(#bg)"/>'
    b'<circle cx="150" cy="120" r="68" fill="none" stroke="#fff" stroke-width="2" opacity="0.12"/>'
    b'<circle cx="150" cy="120" r="50" fill="none" stroke="#fff" stroke-width="2" opacity="0.08"/>'
    b'<path d="M150 55 L150 135 M118 108 L150 142 L182 108" stroke="url(#ar)" stroke-width="13" stroke-linecap="round" stroke-linejoin="round" fill="none"/>'
    b'<rect x="110" y="150" width="80" height="10" rx="5" fill="#27ae60"/>'
    b'<rect x="78" y="178" width="144" height="12" rx="6" fill="#2ecc71" opacity="0.55"/>'
    b'<rect x="78" y="198" width="104" height="12" rx="6" fill="#2ecc71" opacity="0.42"/>'
    b'<rect x="78" y="218" width="64"  height="12" rx="6" fill="#2ecc71" opacity="0.28"/>'
    b'<path d="M91 184 L101 194 L116 179" stroke="#2ecc71" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>'
    b'<path d="M91 204 L101 214 L116 199" stroke="#2ecc71" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>'
    b'</svg>'
)

# ══════════════ Embedded App Icon (PNG, base64) ══════════════
APP_ICON_B64 = "iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAYAAABccqhmAAAMfUlEQVR4nO3dX28T2R3GcbPq7VYqcTwJgvp+l92lq6oFkSIgiZMUhQv2LVSquG61gkXVqqpot9VS9aISalX1HZQLECU4CSAKgq1WbUravfcuSjKOQ6XlBdCLeFInxPbM+TPnz+/7kZAQEPvMeJ7nnBnbQ6UCAAAAAAAAAAAAAAAAAADCdcD1AIY59NYPX7keA6Bj7Yu/epszrwZG2CGFL6XgxSAIPqRyXQTOnpzQA7u5KIPSn5DgA4OVWQSlFsD423OEH8hh/T93SslmKU9C8AE1tovgDZsPXqkQfkCH7fxYLQDCD+izmSNrBUD4AXNs5clKARB+wDwbuTJ+gWH8HcIP2LS+au7CoNEVAOEH7DOZM2MFQPiB8pjKm5ECIPxA+UzkTrsACD/gjm7+rH8QCIC/tK4mjr87y+wPeGD92YJSlpVXAIQf8IdqHjkFAARTKgBmf8A/KrlkBQAIRgEAghW+cjh2jOU/4LONlfzvCLACAAQrVADM/oD/iuSUFQAgGAUACEYBAIJ9o9C/pi6AqOSO9Nj7XAAEQpE3r8zpgGAUACAYBQAIRgEAguV/F+AA1wCB2LACAASjAADBKABAsGKfBESQ1j9fqKv+7Ph3Z1smxwK/UAAR6Rd0nRDbeEz4I3cBvOJkwUsbf/9/QMe+1yeU3dcuuf5W7sdNL34x8DE3Ps/xvPAeK4AA5Qq9Zb3P68N4oIYCCITPIaMMwkUBeC4LVChh2q8MQhm7RBSAp2IITzb2GLYlVhSAZ2IMC0Xgr/wFwLsAVm087YbjeDccrve3hefPtm2nCI5TBK6xAvDAxtOFuqQw7BSBsO32EQXg0GuzvjBjx2db0veBaxSAI8x+21gNuOX6TFMkDvbX9a4GUB5WACViuTsYpwTl445AJdl4crc+dmJm+6Au/H8yO+Do9c720cbTnv0FazgFKMGu8LsbQ2Lz35s2dmKmtfHkLqcElnEKYJmL8O8X3rETM2ny+7dzP8bYiZm03+NoDq/IGFo+lGfMKACLyjx4e8NqKqT7PY6N5xkyBkrAIgrAkrIO2iyQZc3Mvc9T1nNTAvZQABbYPljLnoX7yZ67jPFQAnZwRyDD0sd368nJmZaNy6vp4+2gJSd7QmbpdSnyeveOJ32yzxgNSU7OtNIn3f0LI4i1QTvht/PYSXJyJrURLJOyMWZlZeHxW+lj3h0whVMAz+076wegtwRCG7skrAAMsTH7hzLr92NrNcAqwBwKwACb4Tf5mK5QAv4q8FFgi6MIWProbj2ZmGmZ2j/po+6yeWImdbrPDT93MtFzSjBhptiSie0SSCa4KKiKawAeSR/dTUyFw0fZtsW+nSHhFEDDzuxv5rHEhCKZmEmzlY6Bx2qljzgVUEUBKCL8eigBP1AAjkkMf8ZkCUANBaDA1OwvOfwZUyXAKkBNgduCc0OQXUztD1/3a9njin1/eooVQEHpw2Y9OdXQn/0fNpPkVEP07J9JTjXS9GFTfxVwqtFKHzZZBRRAAThA+F9nqgRQDAVQgInZn/D3Z6IEWAUUQwEAglEAOTH7l4NVQLm4IUgBOvug/aCZ1E430lAq1+XrXTvdSNsPu/tLA8fscOyiAIxfO+p6CEpCHbckFEAO7QfNeu20+vJ/Z/ZXkIUotDDpjrt2upG2H6ifCtRON1rtB5wGDEMBBCSUEghlnKAAvLZfkHwPV4hjlowCGMLV8n9QaMavHfUuVMPGpDJeTgPsy18AB4T+0t12hZ/PG5bxa0eLjyUvH8braP9H8ysHVgAWte83k9oZu+/7j3/qdiVg+/lrZxpp+z4fEbaFAhigfb9Zr53R/+JPESqBclUCIYy1dqbRat/nNKAfCsAjOuEoO1ghjRX9UQCWqCz/13/6b63nLCtYus9TdDs5DbCHAvCM7yVQdvhhF3cEGkZnuxV/dv3D1cr4b95RftrxT49W1j9cVf75SqWy79h1xlSpbG+X1pTj4LWIHf8vgKeyAKuGLvs57SLQGEPGxBhgB6cAfbSXF+u1yelS3wHYj254dMMbQ/hrk9Ot9vIi7wTsgwKwoL28mNQmp429/++qBHwKf21yOm0vL3Ih0DAKIBBll4BP4Yc9FEBAQglVKOMEdwQaSGebbe2vtUurlUOf6M3ONq1d0rzSP4SPr0nI2CUBWrvk5wzr67jQHwUQKN/C5tt4kA+fAwhYFjqXpwQEP2ysACLgKoSEP3wUQCTKDiPhj0P+U4Cid5SJgc42O9hfa5dXK4d+Zf90YO3yqrvjIbDXxHesACKzdtnuzGz78VEuCiBCtkJK+ONDAUTKdFgJf5woAAtGG9PpZtP9F1dMhdaH8G82F5PRhrkvWGEbBdDHaGO6tdkM/yuka5dXBwZ42N/5EH5dm83F+mjD/Ve7fcQdgYaJ5C40a1eeVQ5dffe1P6u8MfjvvBLJa+ET315iWLR25ZnRf4fwUQDCZOHeG/J+f464UQCWjM5OpZsLS84vBO6nX8h9Df/mwlIyOjvFBUALKABAMApggNHZqdbmwlLw7wRItrmwVB+dneIdgD7y3xFI8OeoVbe9OjeVdhaWkuocy1dVnTvd/adx/Ek+dodhBQAIRgEMUZ2banXuqJ8GVOem0s4dPy8G+m5n9lf/+Xp1juX/IBQAIBgFAAhGAeTAaUD5WP6Xo8B3ASyOIhS6+4B9WAz72zp2UUmq56bSzm1WAXl0bi8l1XO8dVoGCiCn6rmpVue23oeCKIHhTIS/c3upXj3H8j8PCgAQjAIogFWAXcz+5eOGICo090V1fjLt3F5OqvOTnOd2dW5194eJKYljNTdWAAVV5ydbnVvL2l8Qqs5Ppp1by6wEKj3h13+cenV+ktm/AAoAEIwCUMAqwBxmf7coAMckl4Cp8EMdBaDI1Cqg+1jiSsBk+Jn91eW+VcLB+bNcWt3H1s3l+sh5Mwff1s3lZOR8/DOiye00uf9j8+LWvaH5zv82IKwbOT+Zbt3cXgnEWAQxb1uoWAEYYGMWim01YGN7mP0Hy7MC4BqAASPnJ1tbN81cD+h5zJ3VQOgIv79YAWg4/PF7roeASqXy/Of/cj0EL7ECsIjw+4PXQh3fBVBw+GfHXA8Bexz++L3K81+suB5GcFgBFET4/cVrUxwFAAhGAQCCUQCAYBQAIBi3BS/o+dWVyuErx1wPA/t4fnWF47QgdpeC51dXXA8Be/CaqKEAFHHA+YPXQh3fBtSgc+Bt3bhXH7lwls+yd7E/3KAAHBm5cLa1deNePfu96/G4wj5wiwJwKDvopc5+UrfbJ7kL4FXu7w2iqIMfnG296M6EBz+IPxAv/tKzrRxXTrEC8EQW/F3hiEzM2xYqCsAzMRZBTNsSGwrAUzEUQchjl4IC8NzeIuj9Mx+FMk5sy30J5lsXznBHkD2OfHTsM9djCMVXv1z5vusxSPPfG/cN3hacOwLtcuTSdwh/AUc+OvbZV5/8kxLwDB8FVkD41bDf/EMBFMRBrIf95xcKABCMAgAEowAAwfK/C8BntmEKx5I3WAEU9NWveStLB/vPLxSAAg5iNew3/1AAijiYi2F/+YnvAmjgoEboWAEAguW/IxBVAUSHWAOCUQCAYBQAIBgFAAhGAQCCcUcgDd/+yfvXXY9BxZfX/nHR9RjgB1YAikINf6US9thhFgWgIIYAxbAN0EcBFBRTcGLaFqihAADBKABAMO4IJB2vq2isAADBKICCvvxtPO+hx7QtUEMBKIghODFsA/RRAIpCDlDIY4dZ3BBEQ+t3gQaJ1xJdHAqAYBQAIBgFAAhGAQCCUQCAYNwQBBCMFQAgGAUACEYBAIJRAIBgFAAgGDcEAQRjBQAIRgEAglEAgGAUACAYBQAIxh2BAMGINSAYBQAIRgEAglEAgGAUACBYge8CcEcgIDa5VwBf//lvfB0ICETevHIKAAhGAQCCUQCAYBQAIFjhC3vf/NEPeDsA8NjXf8p/wZ4VACBY4QIo0i4AylU0n6wAAMEoAEAwpQLgNADwj0ou838XYA/uEASETznGL//IKgDwhWoeteZxSgBwTyeHLOQBwbQLgFUA4I5u/oysACgBoHwmcmc0uG/+eILvCQAlePmHR0aya/QagKlBAejPZM6MXwSkBAB7TOfLyrsAlABgno1cWXsbkBIAzLGVJ6ufA6AEAH02c1RKQN+8yLsDgIqX1+1OoqXO0BQBkI/t4GdK/ShwWRsFhKzMnDgLJKsBYDcXE6QXMzJlAKlcr4q9KIAMRQApXAc/48UgBqEUEDpfwg4AAAAAAAAAAAAAAAAgUv8DsBE5pmUwsyoAAAAASUVORK5CYII="

def get_app_icon() -> QIcon:
    """טוען את אייקון האפליקציה המוטמע (PNG ללא רקע לבן)"""
    try:
        data = base64.b64decode(APP_ICON_B64)
        pix = QPixmap()
        pix.loadFromData(data)
        if not pix.isNull():
            return QIcon(pix)
    except Exception:
        pass
    return QIcon()

class SplashWindow(QWidget):
    """חלונית פתיחה מעוצבת"""
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint|Qt.SplashScreen)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(380,420)
        screen=QApplication.primaryScreen().geometry()
        self.move(screen.center()-QPoint(190,210))
        self._build()

    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(24,28,24,28)
        lay.setAlignment(Qt.AlignCenter); lay.setSpacing(10)

        # אייקון
        img=QLabel(); img.setAlignment(Qt.AlignCenter)
        ico=get_app_icon()
        if not ico.isNull():
            pix=ico.pixmap(140,140)
            img.setPixmap(pix)
        else:
            img.setText("💿"); img.setStyleSheet("font-size:80px;")
        lay.addWidget(img,alignment=Qt.AlignCenter)

        # שם התוכנה
        name_lbl=QLabel(APP_NAME); name_lbl.setAlignment(Qt.AlignCenter)
        name_lbl.setStyleSheet("font-size:18px;font-weight:bold;color:#1a252f;letter-spacing:1px;margin-top:4px;")
        lay.addWidget(name_lbl)

        # גרסה
        ver_lbl=QLabel(f"גרסה {APP_VER}"); ver_lbl.setAlignment(Qt.AlignCenter)
        ver_lbl.setStyleSheet("font-size:12px;color:#7f8c8d;margin-bottom:14px;")
        lay.addWidget(ver_lbl)

        # פס טעינה
        self.prog=QProgressBar(); self.prog.setRange(0,0)
        self.prog.setFixedHeight(6); self.prog.setTextVisible(False)
        self.prog.setStyleSheet("""
            QProgressBar{border:none;border-radius:3px;background:#dce3ea;}
            QProgressBar::chunk{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #27ae60,stop:1 #2ecc71);border-radius:3px;}
        """)
        lay.addWidget(self.prog)

        loading_lbl=QLabel("טוען..."); loading_lbl.setAlignment(Qt.AlignCenter)
        loading_lbl.setStyleSheet("font-size:11px;color:#95a5a6;")
        lay.addWidget(loading_lbl)

    def paintEvent(self,e):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        # צל עדין
        shadow_rect=self.rect().adjusted(4,4,-4,-4)
        p.setBrush(QColor(0,0,0,20)); p.setPen(Qt.NoPen)
        p.drawRoundedRect(shadow_rect,18,18)
        # רקע לבן עם גבול עדין
        main_rect=self.rect().adjusted(0,0,-4,-4)
        p.setBrush(QColor(252,253,255,250))
        p.setPen(QPen(QColor(220,225,235),1))
        p.drawRoundedRect(main_rect,16,16)
        # פס צבע עליון
        top_rect=QRect(main_rect.x(),main_rect.y(),main_rect.width(),5)
        grad=QLinearGradient(top_rect.topLeft(),top_rect.topRight())
        grad.setColorAt(0,QColor(39,174,96)); grad.setColorAt(1,QColor(46,204,113))
        p.setBrush(grad); p.setPen(Qt.NoPen)
        p.drawRoundedRect(top_rect,16,16)


# ══════════════ Small Dialogs ══════════════
class PasswordDialog(QDialog):
    def __init__(self,title="סיסמה",parent=None):
        super().__init__(parent); self.setWindowTitle(title)
        self.setLayoutDirection(get_dir()); self.setMinimumWidth(340)
        self.setWindowFlags(self.windowFlags()&~Qt.WindowContextHelpButtonHint)
        lay=QVBoxLayout(self)
        lay.addWidget(QLabel("Password:" if CONFIG.data.get("language","he")=="en" else "סיסמה:"))
        self.pw=QLineEdit(); self.pw.setEchoMode(QLineEdit.Password); lay.addWidget(self.pw)
        btns=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject); lay.addWidget(btns)
        self.pw.returnPressed.connect(self.accept)
    def get_password(self): return self.pw.text()


class CustomSilentTypeDialog(QDialog):
    def __init__(self,data=None,parent=None):
        super().__init__(parent)
        self.setWindowTitle("הוספת סוג התקנה שקטה" if not data else "עריכת סוג")
        self.setLayoutDirection(get_dir()); self.setMinimumWidth(440); self._data=data or {}
        lay=QFormLayout(self)
        self.name_e=QLineEdit(data.get("name","") if data else "")
        self.name_e.setPlaceholderText("שם הסוג, למשל: MyApp Silent")
        self.args_e=QLineEdit(data.get("args","") if data else "")
        self.args_e.setPlaceholderText("ארגומנטים, למשל: /quiet /norestart")
        lay.addRow("שם הסוג:",self.name_e); lay.addRow("ארגומנטים:",self.args_e)
        btns=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        btns.accepted.connect(self._ok); btns.rejected.connect(self.reject); lay.addRow(btns)
    def _ok(self):
        if not self.name_e.text().strip(): show_warning(self,"שגיאה","יש להזין שם."); return
        self.accept()
    def get_data(self):
        return {"id":self._data.get("id",str(datetime.datetime.now().timestamp())),
                "name":self.name_e.text().strip(),"args":self.args_e.text().strip()}


# ══════════════ Post-action editor ══════════════
class PostActionsEditor(QDialog):
    """עריכת פעולות לאחר התקנה"""
    def __init__(self,actions=None,parent=None):
        super().__init__(parent)
        self.setWindowTitle("פעולות לאחר התקנה")
        self.setLayoutDirection(get_dir()); self.setMinimumSize(580,420)
        self.actions=list(actions or [])
        self._build(); self._refresh()

    def _build(self):
        lay=QVBoxLayout(self)
        note=QLabel("הוסף פעולות שירוצו אוטומטית לאחר ההתקנה (EXE/MSI/CMD, בשקט מלא)")
        note.setStyleSheet("color:#555;font-size:11px;"); lay.addWidget(note)
        bar=QHBoxLayout()
        for lbl,fn in [("➕ הוסף",self._add),("✏️ ערוך",self._edit),("🗑️ מחק",self._delete),("⬆️",self._up),("⬇️",self._dn)]:
            b=QPushButton(lbl); b.clicked.connect(fn); bar.addWidget(b)
        bar.addStretch(); lay.addLayout(bar)
        self.lst=QListWidget(); lay.addWidget(self.lst)
        btns=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject); lay.addWidget(btns)

    def _refresh(self):
        self.lst.clear()
        for a in self.actions:
            typ=a.get("type","exe"); cmd=a.get("cmd",""); desc=a.get("desc","")
            item=QListWidgetItem(f"[{typ.upper()}] {desc or cmd}")
            item.setData(Qt.UserRole,a); self.lst.addItem(item)

    def _add(self):
        dlg=PostActionEditDialog(parent=self)
        if dlg.exec_()==QDialog.Accepted:
            self.actions.append(dlg.get_data()); self._refresh()

    def _edit(self):
        item=self.lst.currentItem()
        if not item: return
        r=self.lst.currentRow()
        dlg=PostActionEditDialog(data=self.actions[r],parent=self)
        if dlg.exec_()==QDialog.Accepted:
            self.actions[r]=dlg.get_data(); self._refresh()

    def _delete(self):
        r=self.lst.currentRow()
        if r<0: return
        self.actions.pop(r); self._refresh()

    def _up(self):
        r=self.lst.currentRow()
        if r>0: self.actions.insert(r-1,self.actions.pop(r)); self._refresh(); self.lst.setCurrentRow(r-1)

    def _dn(self):
        r=self.lst.currentRow()
        if r<len(self.actions)-1: self.actions.insert(r+1,self.actions.pop(r)); self._refresh(); self.lst.setCurrentRow(r+1)

    def get_actions(self): return self.actions


class PostActionEditDialog(QDialog):
    def __init__(self,data=None,parent=None):
        super().__init__(parent)
        self.setWindowTitle("עריכת פעולה" if data else "הוספת פעולה")
        self.setLayoutDirection(get_dir()); self.setMinimumWidth(520)
        self._data=data or {}; self._build()
        if data: self._populate(data)

    def _build(self):
        lay=QFormLayout(self)
        self.type_cb=QComboBox()
        self.type_cb.addItems(["exe — קובץ הרצה/MSI","cmd — פקודת CMD שקטה"])
        self.type_cb.currentIndexChanged.connect(self._on_type)
        lay.addRow("סוג פעולה:",self.type_cb)
        fr=QHBoxLayout()
        self.cmd_e=QLineEdit(); self.cmd_e.setPlaceholderText("נתיב לקובץ או פקודה")
        browse=QPushButton("עיון..."); browse.clicked.connect(self._browse)
        fr.addWidget(self.cmd_e); fr.addWidget(browse)
        lay.addRow("קובץ / פקודה:",fr)
        self.args_e=QLineEdit(); self.args_e.setPlaceholderText("ארגומנטים (אופציונלי)")
        lay.addRow("ארגומנטים:",self.args_e)
        self.desc_e=QLineEdit(); self.desc_e.setPlaceholderText("תיאור קצר (מוצג בסטטוס)")
        lay.addRow("תיאור:",self.desc_e)
        self.show_cb=QCheckBox("הצג פעולה זו בסטטוס ההתקנה"); self.show_cb.setChecked(True)
        lay.addRow("",self.show_cb)
        self.cmd_note=QLabel("הערה: CMD ירוץ דרך cmd /c ... ללא חלון.")
        self.cmd_note.setStyleSheet("color:#888;font-size:10px;"); lay.addRow("",self.cmd_note)
        btns=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        btns.accepted.connect(self._ok); btns.rejected.connect(self.reject); lay.addRow(btns)

    def _on_type(self,idx):
        self.cmd_note.setVisible(idx==1)

    def _populate(self,d):
        self.type_cb.setCurrentIndex(0 if d.get("type","exe")=="exe" else 1)
        self.cmd_e.setText(d.get("cmd",""))
        self.args_e.setText(d.get("args",""))
        self.desc_e.setText(d.get("desc",""))
        self.show_cb.setChecked(d.get("show_in_status",True))

    def _browse(self):
        path,_=QFileDialog.getOpenFileName(self,"בחר קובץ",SOFTWARE_DIR,"קבצים (*.exe *.msi *.bat *.cmd);;כל (*)")
        if path: self.cmd_e.setText(path)

    def _ok(self):
        if not self.cmd_e.text().strip(): show_warning(self,"שגיאה","יש להזין קובץ/פקודה."); return
        self.accept()

    def get_data(self):
        return {
            "id":self._data.get("id",str(datetime.datetime.now().timestamp())),
            "type":"exe" if self.type_cb.currentIndex()==0 else "cmd",
            "cmd":self.cmd_e.text().strip(),"args":self.args_e.text().strip(),
            "desc":self.desc_e.text().strip(),"show_in_status":self.show_cb.isChecked()
        }


# ══════════════ AutoTrialDialog ══════════════
class AutoTrialDialog(QDialog):
    """חלון מעקב לניסוי אוטומטי של כל סוגי ההתקנה השקטה"""
    result_args = pyqtSignal(str, str)   # (silent_type, silent_args) when found

    def __init__(self, fp, presets, parent=None):
        super().__init__(parent)
        self.fp = fp
        self.presets = presets  # list of (name, args)
        self.setWindowTitle("ניסוי אוטומטי — זיהוי התקנה שקטה")
        self.setLayoutDirection(get_dir())
        self.setMinimumSize(520, 380)
        self._stopped = False
        self._found_name = ""
        self._found_args = ""
        self._build_ui()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        title = QLabel(f"🔍 בודק: {os.path.basename(self.fp)}")
        title.setStyleSheet("font-weight:bold;font-size:13px;color:#2c3e50;")
        lay.addWidget(title)
        note = QLabel(f"יבדוק {len(self.presets)} סוגים לפי הסדר. ⚠️ ההתקנה תרוץ בפועל!")
        note.setStyleSheet("color:#e67e22;font-size:11px;")
        lay.addWidget(note)
        self.prog = QProgressBar(); self.prog.setRange(0, len(self.presets)); self.prog.setValue(0)
        lay.addWidget(self.prog)
        self.current_lbl = QLabel("מתחיל...")
        self.current_lbl.setStyleSheet("color:#2980b9;font-size:12px;")
        lay.addWidget(self.current_lbl)
        # לוג
        self.log = QTextEdit(); self.log.setReadOnly(True)
        self.log.setStyleSheet("background:#1e1e2e;color:#cdd6f4;font-family:Consolas;font-size:11px;")
        self.log.setMinimumHeight(160)
        lay.addWidget(self.log)
        # כפתורים
        btn_row = QHBoxLayout()
        self.stop_btn = QPushButton("⏹ עצור")
        self.stop_btn.setStyleSheet("background:#e74c3c;color:white;font-weight:bold;border-radius:4px;padding:6px 16px;")
        self.stop_btn.clicked.connect(self._stop)
        self.cont_btn = QPushButton("▶ המשך")
        self.cont_btn.setStyleSheet("background:#27ae60;color:white;font-weight:bold;border-radius:4px;padding:6px 16px;")
        self.cont_btn.setVisible(False)
        self.cont_btn.clicked.connect(self._continue)
        self.close_btn = QPushButton("✖ סגור")
        self.close_btn.setVisible(False)
        self.close_btn.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(self.stop_btn)
        btn_row.addWidget(self.cont_btn)
        btn_row.addWidget(self.close_btn)
        lay.addLayout(btn_row)
        self._wait_event = threading.Event()
        # הפעל ב-thread
        t = threading.Thread(target=self._run_trials, daemon=True)
        t.start()

    def _log(self, text, color="#cdd6f4"):
        self.log.append(f'<span style="color:{color};">{text}</span>')

    def _stop(self):
        self._stopped = True
        self._wait_event.set()
        self.stop_btn.setVisible(False)
        self.cont_btn.setVisible(False)
        self.close_btn.setVisible(True)
        self.current_lbl.setText("⏹ עצר על ידי המשתמש")

    def _continue(self):
        self.cont_btn.setVisible(False)
        self.stop_btn.setVisible(True)
        self._wait_event.set()

    def _run_trials(self):
        for idx, (name, args) in enumerate(self.presets):
            if self._stopped:
                break
            QMetaObject.invokeMethod(self, "_update_progress",
                Qt.QueuedConnection,
                Q_ARG(int, idx), Q_ARG(str, f"מנסה [{idx+1}/{len(self.presets)}]: {name}  ({args})"))
            cmd = (["msiexec","/i",self.fp]+args.split()) if self.fp.lower().endswith(".msi") else ([self.fp]+args.split() if args else [self.fp])
            try:
                rc = subprocess.run(cmd, timeout=60).returncode
                if rc in (0, 3010):
                    self._found_name = name
                    self._found_args = args
                    QMetaObject.invokeMethod(self, "_on_success",
                        Qt.QueuedConnection,
                        Q_ARG(str, name), Q_ARG(str, args), Q_ARG(int, rc))
                    # המתן להחלטת המשתמש
                    self._wait_event.clear()
                    self._wait_event.wait()
                    if self._stopped:
                        break
                else:
                    QMetaObject.invokeMethod(self, "_on_fail",
                        Qt.QueuedConnection,
                        Q_ARG(str, name), Q_ARG(int, rc))
            except subprocess.TimeoutExpired:
                QMetaObject.invokeMethod(self, "_on_timeout",
                    Qt.QueuedConnection, Q_ARG(str, name))
            except Exception as e:
                QMetaObject.invokeMethod(self, "_on_error",
                    Qt.QueuedConnection, Q_ARG(str, str(e)))
        QMetaObject.invokeMethod(self, "_on_done", Qt.QueuedConnection)

    @pyqtSlot(int, str)
    def _update_progress(self, idx, text):
        self.prog.setValue(idx)
        self.current_lbl.setText(text)
        self.current_lbl.setStyleSheet("color:#2980b9;font-size:12px;")

    @pyqtSlot(str, str, int)
    def _on_success(self, name, args, rc):
        self._log(f"✅ הצליח! {name}  [{args}]  קוד: {rc}", "#2ecc71")
        self.current_lbl.setText(f"✅ נמצא! {name} — {args}")
        self.current_lbl.setStyleSheet("color:#27ae60;font-size:12px;font-weight:bold;")
        # שלח תוצאה מיד כשנמצאה — בלי לחכות לסיום כל הניסויים
        self.result_args.emit(name, args)
        self.stop_btn.setVisible(True)
        self.cont_btn.setVisible(True)

    @pyqtSlot(str, int)
    def _on_fail(self, name, rc):
        self._log(f"❌ נכשל: {name}  קוד: {rc}", "#e74c3c")

    @pyqtSlot(str)
    def _on_timeout(self, name):
        self._log(f"⏱️ פג זמן: {name}", "#e67e22")

    @pyqtSlot(str)
    def _on_error(self, e):
        self._log(f"⚠️ שגיאה: {e}", "#f39c12")

    @pyqtSlot()
    def _on_done(self):
        self.prog.setValue(len(self.presets))
        if self._found_name:
            self.current_lbl.setText(f"✅ הושלם — {self._found_name}  [{self._found_args}]")
            self.result_args.emit(self._found_name, self._found_args)  # תמיד שלח תוצאה אם נמצאה
        elif not self._stopped:
            self.current_lbl.setText("❌ לא נמצאה התקנה שקטה מתאימה")
            self.current_lbl.setStyleSheet("color:#e74c3c;font-size:12px;")
        self.stop_btn.setVisible(False)
        self.cont_btn.setVisible(False)
        self.close_btn.setVisible(True)


# ══════════════ SoftwareEditDialog ══════════════
class SoftwareEditDialog(QDialog):
    def __init__(self,sw_data=None,categories=None,parent=None):
        super().__init__(parent)
        self.setWindowTitle("עריכת תוכנה" if sw_data else "הוספת תוכנה")
        self.setLayoutDirection(get_dir()); self.setMinimumWidth(680)
        self.categories=categories or []; self.icon_path=""; self.sw_data=sw_data or {}
        self._post_actions=list(sw_data.get("post_actions",[]) if sw_data else [])
        self._build_ui()
        if sw_data: self._populate(sw_data)

    def _build_ui(self):
        lay=QFormLayout(self); lay.setLabelAlignment(Qt.AlignRight); lay.setSpacing(10)
        self.name_e=QLineEdit(); lay.addRow("שם התוכנה:",self.name_e)
        # תגיות
        self.tags_e=QLineEdit(); self.tags_e.setPlaceholderText("תגיות מופרדות בפסיק, למשל: אופיס,עריכה,מסמכים")
        lay.addRow("תגיות:",self.tags_e)
        # פרטים טכניים
        self.tech_e=QLineEdit()
        self.tech_e.setLayoutDirection(Qt.RightToLeft)   # שמור RTL גם עם תווים לועזיים
        lang=CONFIG.data.get("language","he")
        if lang=="he":
            self.tech_e.setPlaceholderText("וי עברית, איקס דורש רשיון, שאלה נדרש הפעלה מחדש")
        else:
            self.tech_e.setPlaceholderText("V Hebrew, X Requires license, ? Needs reboot  (comma-separated)")
        lay.addRow("פרטים טכניים:",self.tech_e)
        if lang=="he":
            tech_note=QLabel("ℹ️ כתוב 'וי' לסמל ✅ | 'איקס' לסמל ❌ | 'שאלה' לסמל ❓  (הפרד בפסיק)")
        else:
            tech_note=QLabel("ℹ️ Use 'V' for ✅ | 'X' for ❌ | '?' for ❓  (comma-separated)")
        tech_note.setStyleSheet("color:#888;font-size:10px;"); lay.addRow("",tech_note)
        self.desc_e=QTextEdit(); self.desc_e.setMaximumHeight(50); lay.addRow("תיאור:",self.desc_e)
        # אודות ומקור
        self.about_e=QTextEdit(); self.about_e.setMaximumHeight(50)
        self.about_e.setPlaceholderText("טקסט חופשי: יצרן, גרסה, מידע נוסף...")
        lay.addRow("אודות:",self.about_e)
        self.source_url_e=QLineEdit()
        self.source_url_e.setPlaceholderText("https://example.com")
        lay.addRow("קישור מקור:",self.source_url_e)

        # קובץ + תיבת נתיב מוחלט
        fr=QHBoxLayout()
        self.file_e=QLineEdit()
        # file_e: Read-only + מציג נתיב יחסי ישירות
        self.file_e.setReadOnly(True)
        self.file_e.setStyleSheet("background:#f0f4f8;color:#2c3e50;font-size:11px;")
        browse=QPushButton("בחר..."); browse.clicked.connect(self._browse_file)
        fr.addWidget(self.file_e); fr.addWidget(browse)
        lay.addRow("קובץ התקנה:",fr)
        # תיבת סימון נתיב מוחלט
        self.abs_cb=QCheckBox("נתיב מוחלט (לא יחסי)")
        self.abs_cb.setToolTip("סמן אם הקובץ אינו בתיקיית software\\")
        self.abs_cb.stateChanged.connect(self._on_abs_changed)
        lay.addRow("",self.abs_cb)

        self.cat_cb=QComboBox(); self.cat_cb.addItems([c["name"] for c in self.categories])
        self.cat_cb.setEditable(True); lay.addRow("קטגוריה:",self.cat_cb)

        # התקנה שקטה – לא משנה ארגומנטים בעת בחירת קובץ אם כבר הוגדרו
        sr=QHBoxLayout()
        self.stype_cb=QComboBox(); self._reload_stype()
        self.stype_cb.currentTextChanged.connect(self._on_stype_change)
        self.sargs_e=QLineEdit(); self.sargs_e.setPlaceholderText("ארגומנטים")
        ab=QPushButton("🔍 זיהוי"); ab.clicked.connect(self._auto_detect)
        tb=QPushButton("🧪 ניסוי"); tb.setToolTip("נסה את הארגומנט הנוכחי"); tb.clicked.connect(self._test_silent)
        auto_tb=QPushButton("🤖 ניסוי אוטומטי"); auto_tb.setToolTip("נסה את כל סוגי ההתקנה השקטה לפי הסדר")
        auto_tb.clicked.connect(self._auto_trial)
        for w in [self.stype_cb,self.sargs_e,ab,tb,auto_tb]: sr.addWidget(w)
        lay.addRow("התקנה שקטה:",sr)
        self.sil_lbl=QLabel(""); self.sil_lbl.setStyleSheet("color:#555;font-size:11px;")
        lay.addRow("",self.sil_lbl)

        # פעולות לאחר התקנה
        pa_row=QHBoxLayout()
        self.pa_lbl=QLabel("0 פעולות")
        pa_btn=QPushButton("✏️ ערוך פעולות לאחר התקנה"); pa_btn.clicked.connect(self._edit_post_actions)
        pa_row.addWidget(self.pa_lbl); pa_row.addWidget(pa_btn); pa_row.addStretch()
        lay.addRow("פעולות לאחר:",pa_row)

        # קיצור דרך לאחר התקנה
        self.shortcut_cb=QCheckBox("טען קיצור דרך משולחן העבודה לאחר ההתקנה")
        self.shortcut_cb.setToolTip("בהתקנה שקטה — יאתר אוטומטית את קיצור הדרך/קובץ ההרצה שנוצר ויזכור אותו")
        self.shortcut_cb.stateChanged.connect(self._on_shortcut_toggle)
        lay.addRow("",self.shortcut_cb)
        sc_row=QHBoxLayout()
        self.shortcut_path_e=QLineEdit(); self.shortcut_path_e.setReadOnly(True)
        self.shortcut_path_e.setPlaceholderText("יזוהה אוטומטית לאחר ההתקנה, או לחץ 'זהה עכשיו'")
        self.shortcut_path_e.setStyleSheet("background:#f0f4f8;color:#2c3e50;font-size:11px;")
        sc_detect_btn=QPushButton("🔍 זהה עכשיו"); sc_detect_btn.setToolTip("חפש קיצור דרך קיים בשולחן העבודה או קובץ הרצה מותקן, לפי שם התוכנה")
        sc_detect_btn.clicked.connect(self._detect_shortcut_now)
        sc_clear_btn=QPushButton("✖ נקה"); sc_clear_btn.clicked.connect(self._clear_shortcut_path)
        sc_row.addWidget(self.shortcut_path_e); sc_row.addWidget(sc_detect_btn); sc_row.addWidget(sc_clear_btn)
        self.shortcut_row_w=QWidget(); self.shortcut_row_w.setLayout(sc_row)
        lay.addRow("קיצור דרך:",self.shortcut_row_w)
        self.shortcut_status_lbl=QLabel(""); self.shortcut_status_lbl.setStyleSheet("color:#888;font-size:10px;")
        lay.addRow("",self.shortcut_status_lbl)
        self.shortcut_path_e.setEnabled(False); sc_detect_btn.setEnabled(False); sc_clear_btn.setEnabled(False)
        self._sc_detect_btn=sc_detect_btn; self._sc_clear_btn=sc_clear_btn

        # אייקון
        ir=QHBoxLayout()
        self.icon_lbl=QLabel(); self.icon_lbl.setFixedSize(48,48)
        self.icon_lbl.setStyleSheet("border:1px solid #ccc;background:#f5f5f5;border-radius:4px;")
        for lbl,fn in [("📁 בחר",self._browse_icon),("🖼️ שאב מ-EXE",self._extract_icon),("✖ נקה",self._clear_icon)]:
            b=QPushButton(lbl); b.clicked.connect(fn); ir.addWidget(b)
        ir.insertWidget(0,self.icon_lbl); ir.addStretch()
        lay.addRow("אייקון:",ir)

        btns=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        btns.accepted.connect(self._ok); btns.rejected.connect(self.reject); lay.addRow(btns)

    def _reload_stype(self):
        cur=self.stype_cb.currentText() if self.stype_cb.count() else ""
        self.stype_cb.blockSignals(True); self.stype_cb.clear()
        self.stype_cb.addItems(list(get_all_presets().keys()))
        if cur:
            idx=self.stype_cb.findText(cur)
            if idx>=0: self.stype_cb.setCurrentIndex(idx)
        self.stype_cb.blockSignals(False)

    def _populate(self,d):
        self.name_e.setText(d.get("name",""))
        self.tags_e.setText(d.get("tags",""))
        self.tech_e.setText(d.get("tech_info",""))
        self.desc_e.setText(d.get("description",""))
        self.about_e.setText(d.get("about_text",""))
        self.source_url_e.setText(d.get("source_url",""))
        fp=CONFIG.resolve_file(d.get("file",""))
        # קבע אם נתיב מוחלט
        force_abs=d.get("force_absolute",False)
        self.abs_cb.setChecked(force_abs)
        # _update_hint יגדיר גם את file_e לפי מצב יחסי/מוחלט
        self._stored_abs_path=fp   # שמור את הנתיב המוחלט האמיתי לשימוש ב-get_data
        self._update_hint(fp)
        cat=d.get("category","")
        idx=self.cat_cb.findText(cat)
        if idx>=0: self.cat_cb.setCurrentIndex(idx)
        else: self.cat_cb.setCurrentText(cat)
        self.sargs_e.setText(d.get("silent_args",""))
        st=d.get("silent_type","מותאם אישית")
        idx2=self.stype_cb.findText(st)
        if idx2>=0: self.stype_cb.setCurrentIndex(idx2)
        self.icon_path=resolve_icon(d.get("icon","")) or d.get("icon",""); self._refresh_icon()
        self._post_actions=list(d.get("post_actions",[]))
        self._upd_pa_lbl()
        auto_sc=d.get("auto_shortcut",False)
        self.shortcut_cb.setChecked(auto_sc)
        self.shortcut_path_e.setText(d.get("shortcut_path",""))
        self._on_shortcut_toggle(Qt.Checked if auto_sc else Qt.Unchecked)
        if auto_sc and d.get("shortcut_path",""):
            self.shortcut_status_lbl.setText("✅ נתיב שמור מהפעם הקודמת")
            self.shortcut_status_lbl.setStyleSheet("color:#27ae60;font-size:10px;")

    def _upd_pa_lbl(self):
        n=len(self._post_actions)
        self.pa_lbl.setText(f"{n} פעולות" if n else "ללא פעולות")

    def _on_abs_changed(self,_):
        self._update_hint(self.file_e.text())

    def _on_stype_change(self,text):
        p=get_all_presets()
        if text in p: self.sargs_e.setText(p[text])

    def _browse_file(self):
        path,_=QFileDialog.getOpenFileName(self,"בחר קובץ התקנה",SOFTWARE_DIR,
                                           "קבצי התקנה (*.exe *.msi *.bat *.cmd);;כל הקבצים (*)")
        if path:
            self._stored_abs_path=path   # שמור נתיב מוחלט אמיתי
            self._update_hint(path)       # יציג יחסי/מוחלט בשורת הבחירה
            if not self.name_e.text():
                self.name_e.setText(os.path.splitext(os.path.basename(path))[0])
            # ← לא משנה silent_args אם כבר הוגדרו
            if not self.sargs_e.text().strip():
                self._auto_detect_quiet()
            if not self.icon_path:
                ex=extract_icon_from_exe(path)
                if ex: self.icon_path=ex; self._refresh_icon()

    def _update_hint(self,path):
        """מעדכן את שורת הקובץ עם הנתיב הנכון (יחסי/מוחלט)"""
        if not path: self.file_e.setText(""); return
        force_abs=self.abs_cb.isChecked()
        rel=CONFIG.make_relative(path,force_absolute=force_abs)
        if force_abs or rel==path:
            # נתיב מוחלט — הצג את הנתיב המלא
            self.file_e.setText(path)
        else:
            # נתיב יחסי — הצג software\filename (או software\subfolder\filename)
            display_rel = os.path.join("software", rel)
            self.file_e.setText(display_rel)

    def _auto_detect_quiet(self):
        """זיהוי שקט (ללא הודעות) — קורא מ-_browse_file"""
        fp=getattr(self,"_stored_abs_path",self.file_e.text())
        if not fp or not os.path.exists(fp): return
        stype,sargs=detect_silent_type(fp)
        if not self.sargs_e.text().strip(): self.sargs_e.setText(sargs)
        idx=self.stype_cb.findText(stype)
        if idx>=0: self.stype_cb.setCurrentIndex(idx)

    def _auto_detect(self):
        """זיהוי לפי מבנה הקובץ (header) — ללא הרצה"""
        fp=getattr(self,"_stored_abs_path","")
        if not fp: fp=self.file_e.text()
        # נסה לפתור נתיב אם הוא יחסי
        if fp and not os.path.isabs(fp):
            fp2=CONFIG.resolve_file(fp)
            if fp2 and os.path.exists(fp2): fp=fp2
        if not fp or not os.path.exists(fp):
            show_warning(self,"שגיאה","בחר קובץ תחילה (לחץ 'בחר...' ובחר את קובץ ההתקנה)."); return
        stype,sargs=detect_silent_type(fp)
        self.sargs_e.setText(sargs)
        idx=self.stype_cb.findText(stype)
        if idx>=0: self.stype_cb.setCurrentIndex(idx)
        if stype!="מותאם אישית":
            self.sil_lbl.setText(f"✅ זוהה: {stype} — {sargs}")
            self.sil_lbl.setStyleSheet("color:#27ae60;font-size:11px;font-weight:bold;")
        else:
            self.sil_lbl.setText("⚠️ לא זוהה סוג אוטומטי — נסה 'ניסוי אוטומטי' לגילוי בהרצה")
            self.sil_lbl.setStyleSheet("color:#e67e22;font-size:11px;")

    def _auto_trial(self):
        """ניסוי אוטומטי — מנסה את כל הסוגים עם חלון מעקב"""
        fp=getattr(self,"_stored_abs_path",self.file_e.text())
        if not fp or not os.path.exists(fp):
            show_warning(self,"שגיאה","בחר קובץ התקנה תחילה."); return
        presets=get_all_presets()
        trial_list=[(n,a) for n,a in presets.items() if n not in ("מותאם אישית","ללא ארגומנטים")]
        if not trial_list:
            show_info(self,"ניסוי אוטומטי","אין סוגים לבדיקה."); return
        dlg=AutoTrialDialog(fp, trial_list, self)
        dlg.result_args.connect(self._apply_trial_result)
        dlg.exec_()

    def _apply_trial_result(self, stype, sargs):
        """מחיל תוצאת ניסוי אוטומטי מוצלח"""
        self.sargs_e.setText(sargs)
        idx=self.stype_cb.findText(stype)
        if idx>=0: self.stype_cb.setCurrentIndex(idx)
        self.sil_lbl.setText(f"✅ נמצא בניסוי אוטומטי: {stype} — {sargs}")

    def _test_silent(self):
        fp=getattr(self,"_stored_abs_path",self.file_e.text()); args=self.sargs_e.text().strip()
        if not fp or not os.path.exists(fp): show_warning(self,"שגיאה","בחר קובץ תחילה."); return
        if show_question(self,"ניסוי",f"להריץ:\n{os.path.basename(fp)}  {args}\n\n⚠️ ההתקנה תרוץ בפועל!",
                                QMessageBox.Yes|QMessageBox.No)!=QMessageBox.Yes: return
        self.sil_lbl.setText("⏳ מריץ..."); QApplication.processEvents()
        cmd=["msiexec","/i",fp]+(args.split() if args else []) if fp.lower().endswith(".msi") else [fp]+(args.split() if args else [])
        try:
            rc=subprocess.run(cmd,timeout=180).returncode
            self.sil_lbl.setText(f"✅ הצליח — קוד: {rc}" if rc in (0,3010) else f"❌ שגיאה — קוד: {rc}")
        except subprocess.TimeoutExpired: self.sil_lbl.setText("⚠️ פג זמן")
        except Exception as e: self.sil_lbl.setText(f"❌ {e}")

    def _edit_post_actions(self):
        dlg=PostActionsEditor(self._post_actions,self)
        if dlg.exec_()==QDialog.Accepted:
            self._post_actions=dlg.get_actions(); self._upd_pa_lbl()

    def _on_shortcut_toggle(self,state):
        en=(state==Qt.Checked)
        self.shortcut_path_e.setEnabled(en)
        self._sc_detect_btn.setEnabled(en)
        self._sc_clear_btn.setEnabled(en)
        if en and not self.shortcut_path_e.text().strip():
            self.shortcut_status_lbl.setText("⚡ יזוהה אוטומטית בסיום ההתקנה השקטה, או לחץ 'זהה עכשיו' לבדיקה ידנית")
            self.shortcut_status_lbl.setStyleSheet("color:#888;font-size:10px;")
        elif not en:
            self.shortcut_status_lbl.setText("")

    def _detect_shortcut_now(self):
        """מנסה לאתר קיצור דרך קיים בשולחן העבודה, או EXE מותקן, לפי שם התוכנה"""
        name=self.name_e.text().strip()
        if not name:
            show_warning(self,"שגיאה","הזן שם תוכנה תחילה."); return
        self.shortcut_status_lbl.setText("⏳ מחפש..."); QApplication.processEvents()
        lnk=find_desktop_shortcut(name)
        if lnk:
            self.shortcut_path_e.setText(lnk)
            self.shortcut_status_lbl.setText(f"✅ נמצא קיצור דרך בשולחן העבודה: {os.path.basename(lnk)}")
            self.shortcut_status_lbl.setStyleSheet("color:#27ae60;font-size:10px;font-weight:bold;")
            return
        exe=find_installed_exe(name)
        if exe:
            self.shortcut_path_e.setText(exe)
            self.shortcut_status_lbl.setText(f"✅ נמצא קובץ הרצה מותקן: {os.path.basename(exe)}")
            self.shortcut_status_lbl.setStyleSheet("color:#27ae60;font-size:10px;font-weight:bold;")
        else:
            self.shortcut_status_lbl.setText("⚠️ לא נמצא — נסה שוב לאחר ההתקנה, או שהתקנה השקטה תאתר זאת אוטומטית")
            self.shortcut_status_lbl.setStyleSheet("color:#e67e22;font-size:10px;")

    def _clear_shortcut_path(self):
        self.shortcut_path_e.clear()
        self.shortcut_status_lbl.setText("")

    def _extract_icon(self):
        fp=getattr(self,"_stored_abs_path",self.file_e.text())
        if not fp or not os.path.exists(fp): show_warning(self,"שגיאה","בחר קובץ תחילה."); return
        r=extract_icon_from_exe(fp)
        if r: self.icon_path=r; self._refresh_icon(); self.sil_lbl.setText("✅ אייקון נשאב")
        else: show_info(self, "אייקון","לא ניתן לשאוב. בחר ידנית.")

    def _browse_icon(self):
        path,_=QFileDialog.getOpenFileName(self,"בחר אייקון",ICONS_DIR,"תמונות (*.png *.jpg *.ico *.bmp)")
        if path:
            dest=os.path.join(ICONS_DIR,os.path.basename(path))
            if path!=dest:
                try: shutil.copy2(path,dest)
                except: dest=path
            self.icon_path=dest; self._refresh_icon()

    def _clear_icon(self): self.icon_path=""; self.icon_lbl.clear()
    def _refresh_icon(self):
        rip=resolve_icon(self.icon_path)
        if rip:
            self.icon_lbl.setPixmap(QPixmap(rip).scaled(48,48,Qt.KeepAspectRatio,Qt.SmoothTransformation))
        else: self.icon_lbl.clear()

    def _ok(self):
        if not self.name_e.text().strip(): show_warning(self,"שגיאה","יש להזין שם."); return
        if not self.file_e.text().strip(): show_warning(self,"שגיאה","יש לבחור קובץ."); return
        self.accept()

    def get_data(self):
        # השתמש בנתיב המוחלט האמיתי (לא בתצוגת file_e שיכולה להיות יחסית)
        fp=getattr(self,"_stored_abs_path",self.file_e.text()).strip()
        force_abs=self.abs_cb.isChecked()
        rel=CONFIG.make_relative(fp,force_absolute=force_abs)
        return {
            "id":self.sw_data.get("id",str(datetime.datetime.now().timestamp())),
            "name":self.name_e.text().strip(),
            "tags":self.tags_e.text().strip(),
            "tech_info":self.tech_e.text().strip(),
            "description":self.desc_e.toPlainText().strip(),
            "about_text":self.about_e.toPlainText().strip(),
            "source_url":self.source_url_e.text().strip(),
            "file":rel,"force_absolute":force_abs,
            "category":self.cat_cb.currentText().strip(),
            "silent_type":self.stype_cb.currentText(),
            "silent_args":self.sargs_e.text().strip(),
            "icon":make_icon_relative(self.icon_path),
            "post_actions":self._post_actions,
            "auto_shortcut":self.shortcut_cb.isChecked(),
            "shortcut_path":self.shortcut_path_e.text().strip(),
        }


class CategoryEditDialog(QDialog):
    def __init__(self,cat_data=None,parent=None):
        super().__init__(parent)
        self.setWindowTitle("עריכת קטגוריה" if cat_data else "הוספת קטגוריה")
        self.setLayoutDirection(get_dir()); self.setMinimumWidth(400); self.cat_data=cat_data or {}
        lay=QFormLayout(self)
        self.name_e=QLineEdit(cat_data.get("name","") if cat_data else "")
        self.desc_e=QLineEdit(cat_data.get("description","") if cat_data else "")
        lay.addRow("שם:",self.name_e); lay.addRow("תיאור:",self.desc_e)
        btns=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject); lay.addRow(btns)
    def get_data(self):
        return {"id":self.cat_data.get("id",str(datetime.datetime.now().timestamp())),
                "name":self.name_e.text().strip(),"description":self.desc_e.text().strip()}


# ══════════════ SettingsWindow ══════════════
class SettingsWindow(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"⚙️  {TR('tab_settings')} — {TR('app_name')}")
        self.setLayoutDirection(get_dir()); self.setMinimumSize(960,720)
        # הורש אייקון מהחלון האב
        if parent and parent.windowIcon():
            self.setWindowIcon(parent.windowIcon())
        self._build_ui(); self._refresh_all()

    def _build_ui(self):
        lay=QVBoxLayout(self)
        self.tabs=QTabWidget(); self.tabs.setLayoutDirection(get_dir())
        self.tabs.setStyleSheet("""
            QTabWidget::pane{border:1px solid #d5dce3;background:white;border-radius:0 0 8px 8px;}
            QTabBar::tab{background:#ecf0f1;color:#5d6d7e;padding:9px 20px;
                         border:1px solid #d5dce3;border-bottom:none;
                         font-size:12px;min-width:90px;border-radius:6px 6px 0 0;margin-left:2px;}
            QTabBar::tab:selected{background:white;font-weight:bold;color:#1a252f;border-bottom:2px solid white;}
            QTabBar::tab:hover:!selected{background:#dce3ea;color:#2c3e50;}
        """)
        lay.addWidget(self.tabs)
        self._tab_general(); self._tab_categories(); self._tab_software()
        self._tab_silent(); self._tab_io(); self._tab_security(); self._tab_about()
        sv=QPushButton(TR("save_close")); sv.setMinimumHeight(44)
        sv.setStyleSheet("QPushButton{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #2ecc71,stop:1 #27ae60);"
                         "color:white;font-weight:bold;font-size:14px;border-radius:8px;border:none;}"
                         "QPushButton:hover{background:#2ecc71;}QPushButton:pressed{background:#1e8449;}")
        sv.clicked.connect(self._save_and_close); lay.addWidget(sv)

    # ── כרטיסייה: כללי (שפה בלבד) ────────────────
    def _tab_general(self):
        w=QWidget(); lay=QVBoxLayout(w); lay.setSpacing(14)
        lg=QGroupBox(TR("language")); lb=QHBoxLayout(lg)
        self.lang_he=QRadioButton("עברית 🇮🇱"); self.lang_en=QRadioButton("English 🇺🇸")
        (self.lang_he if CONFIG.data.get("language","he")=="he" else self.lang_en).setChecked(True)
        lb.addWidget(self.lang_he); lb.addWidget(self.lang_en); lb.addStretch()
        lay.addWidget(lg)
        note=QLabel("⚠️ שינוי שפה ייכנס לתוקף בהפעלה הבאה של הכלי.")
        note.setStyleSheet("color:#e67e22;font-size:12px;font-weight:bold;padding:8px;")
        lay.addWidget(note); lay.addStretch()
        self.tabs.addTab(w,TR("tab_general"))

    # ── כרטיסייה: קטגוריות ────────────────────────
    def _tab_categories(self):
        w=QWidget(); lay=QVBoxLayout(w); bar=QHBoxLayout()
        for lbl,fn in [("➕ הוסף",self._add_cat),("✏️ ערוך",self._edit_cat),
                        ("🗑️ מחק סומנים",self._del_cats),("⬆️",self._cat_up),("⬇️",self._cat_dn)]:
            b=QPushButton(lbl); b.clicked.connect(fn); bar.addWidget(b)
        bar.addStretch(); lay.addLayout(bar)
        self.cat_list=QListWidget()
        self.cat_list.setDragDropMode(QListWidget.InternalMove)
        self.cat_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.cat_list.itemDoubleClicked.connect(self._edit_cat)
        lay.addWidget(self.cat_list); self.tabs.addTab(w,TR("tab_categories"))

    # ── כרטיסייה: תוכנות ──────────────────────────
    def _tab_software(self):
        w=QWidget(); lay=QVBoxLayout(w); bar=QHBoxLayout()
        for lbl,fn in [("➕ הוסף",self._add_sw),("➕ מרובות",self._add_multi_sw),
                        ("✏️ ערוך",self._edit_sw),("🗑️ מחק סומנים",self._del_sws),
                        ("⬆️",self._sw_up),("⬇️",self._sw_dn)]:
            b=QPushButton(lbl); b.clicked.connect(fn); bar.addWidget(b)
        bar.addStretch(); lay.addLayout(bar)
        self.sw_list=QListWidget()
        self.sw_list.setDragDropMode(QListWidget.InternalMove)
        self.sw_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.sw_list.itemDoubleClicked.connect(self._edit_sw)
        lay.addWidget(self.sw_list); self.tabs.addTab(w,TR("tab_sw"))

    # ── כרטיסייה: התקנה שקטה ──────────────────────
    def _tab_silent(self):
        w=QWidget(); lay=QVBoxLayout(w); lay.setSpacing(10)
        lay.addWidget(QLabel("סוגי התקנה שקטה מובנים:"))
        bt=QTableWidget(len(BASE_SILENT_PRESETS),2)
        bt.setHorizontalHeaderLabels(["שם","ארגומנטים"])
        bt.horizontalHeader().setStretchLastSection(True)
        bt.setEditTriggers(QTableWidget.NoEditTriggers); bt.setAlternatingRowColors(True)
        for r,(n,a) in enumerate(BASE_SILENT_PRESETS.items()):
            bt.setItem(r,0,QTableWidgetItem(n)); bt.setItem(r,1,QTableWidgetItem(a))
        bt.setMaximumHeight(190); lay.addWidget(bt)
        lay.addWidget(QLabel("סוגים מותאמים אישית:"))
        bar=QHBoxLayout()
        for lbl,fn in [("➕ הוסף",self._add_cst),("✏️ ערוך",self._edit_cst),("🗑️ מחק",self._del_cst)]:
            b=QPushButton(lbl); b.clicked.connect(fn); bar.addWidget(b)
        bar.addStretch(); lay.addLayout(bar)
        self.cst_list=QListWidget(); lay.addWidget(self.cst_list)
        lay.addStretch(); self.tabs.addTab(w,TR("tab_silent"))

    # ── כרטיסייה: ייצוא/ייבוא ─────────────────────
    def _tab_io(self):
        w=QWidget(); lay=QVBoxLayout(w); lay.setSpacing(12)

        # ── נתיב קובץ config ──────────────────────
        cfg_box=QGroupBox("📋 נתיב קובץ הגדרות (config.json)")
        cfg_box.setStyleSheet("QGroupBox{font-weight:bold;color:#2c3e50;}")
        cfg_lay=QVBoxLayout(cfg_box)
        cfg_note=QLabel("ברירת מחדל: software\\config.json (נתיב יחסי, מומלץ לUSB)\nניתן לשנות לנתיב מוחלט לפי הצורך.")
        cfg_note.setStyleSheet("color:#555;font-size:11px;"); cfg_note.setWordWrap(True); cfg_lay.addWidget(cfg_note)
        self._cfg_cur_lbl=QLabel(f"נוכחי: {CONFIG.get_config_path()}")
        self._cfg_cur_lbl.setStyleSheet("color:#2980b9;font-size:11px;font-weight:bold;"); cfg_lay.addWidget(self._cfg_cur_lbl)
        cfg_btn_row=QHBoxLayout()
        default_btn=QPushButton("🔁 שחזר ברירת מחדל")
        def _reset_cfg():
            new_path=os.path.join(SOFTWARE_DIR,"config.json")
            CONFIG.set_config_path(new_path)
            self._cfg_cur_lbl.setText(f"נוכחי: {new_path}")
            show_info(self,"נתיב config","✅ config.json אופס לתיקיית software\\")
        default_btn.clicked.connect(_reset_cfg); cfg_btn_row.addWidget(default_btn)
        custom_btn=QPushButton("📂 בחר נתיב מותאם...")
        def _pick_cfg():
            path,_=QFileDialog.getSaveFileName(self,"בחר מיקום config.json",BASE_DIR,"JSON (*.json)")
            if path:
                CONFIG.set_config_path(path)
                self._cfg_cur_lbl.setText(f"נוכחי: {path}")
                show_info(self,"נתיב config",f"✅ נתיב שונה:\n{path}")
        custom_btn.clicked.connect(_pick_cfg); cfg_btn_row.addWidget(custom_btn)
        cfg_lay.addLayout(cfg_btn_row); lay.addWidget(cfg_box)

        # ── ייצוא / ייבוא ─────────────────────────
        note=QLabel(
            "ייצוא / ייבוא רשימת תוכנות וקטגוריות\n\n"
            "✅ שמור את ההגדרות לקובץ JSON כדי לטעון אותן בגרסה חדשה.\n\n"
            "⚠️ חשוב: לאחר ייבוא, ודא שתיקיית software\\ מכילה את אותם קבצי\n"
            "    התקנה — אחרת הכלי לא יצליח למצוא אותם!"
        )
        note.setWordWrap(True); note.setStyleSheet("color:#2c3e50;font-size:12px;background:#ecf0f1;padding:12px;border-radius:6px;")
        lay.addWidget(note)
        export_btn=QPushButton("📤 ייצא רשימת תוכנות (JSON)"); export_btn.setMinimumHeight(36)
        export_btn.clicked.connect(self._export_sw); lay.addWidget(export_btn)
        import_btn=QPushButton("📥 ייבא רשימת תוכנות (JSON)"); import_btn.setMinimumHeight(36)
        import_btn.clicked.connect(self._import_sw); lay.addWidget(import_btn)
        lay.addStretch(); self.tabs.addTab(w,TR("tab_io"))

    # ── כרטיסייה: אבטחה ───────────────────────────
    def _tab_security(self):
        w=QWidget(); lay=QVBoxLayout(w); form=QFormLayout()
        tr_row=QHBoxLayout()
        self.tool_pw=QLineEdit(); self.tool_pw.setEchoMode(QLineEdit.Password)
        self.tool_pw.setPlaceholderText("הזן סיסמה חדשה...")
        clr1=QPushButton("🗑️ מחק"); clr1.clicked.connect(lambda:self._clr_pw("tool_password"))
        tr_row.addWidget(self.tool_pw); tr_row.addWidget(clr1)
        form.addRow("סיסמת כלי:",tr_row)
        self.tpw_lbl=QLabel(self._pw_s("tool_password")); self.tpw_lbl.setStyleSheet("color:#666;font-size:11px;")
        form.addRow("",self.tpw_lbl)
        sr_row=QHBoxLayout()
        self.sets_pw=QLineEdit(); self.sets_pw.setEchoMode(QLineEdit.Password)
        self.sets_pw.setPlaceholderText("הזן סיסמה חדשה...")
        clr2=QPushButton("🗑️ מחק"); clr2.clicked.connect(lambda:self._clr_pw("settings_password"))
        sr_row.addWidget(self.sets_pw); sr_row.addWidget(clr2)
        form.addRow("סיסמת הגדרות:",sr_row)
        self.spw_lbl=QLabel(self._pw_s("settings_password")); self.spw_lbl.setStyleSheet("color:#666;font-size:11px;")
        form.addRow("",self.spw_lbl)
        sv=QPushButton("💾 שמור סיסמאות"); sv.clicked.connect(self._save_passwords); form.addRow(sv)
        lay.addLayout(form); lay.addStretch(); self.tabs.addTab(w,TR("tab_security"))

    # ── כרטיסייה: אודות ───────────────────────────
    def _tab_about(self):
        w=QWidget(); lay=QVBoxLayout(w)
        lbl=QLabel(TR("about_text")); lbl.setWordWrap(True); lbl.setAlignment(Qt.AlignTop)
        lbl.setStyleSheet("font-size:12px;padding:20px;"); lay.addWidget(lbl); lay.addStretch()
        self.tabs.addTab(w,TR("tab_about"))

    # ── רענון רשימות ──────────────────────────────
    def _refresh_all(self):
        self.cat_list.clear()
        for c in CONFIG.data["categories"]:
            item=QListWidgetItem(f"📂 {c['name']}  —  {c.get('description','')}")
            item.setData(Qt.UserRole,c); self.cat_list.addItem(item)
        self.sw_list.clear()
        for sw in CONFIG.data["software"]:
            ip=sw.get("icon","")
            tags=" ["+sw.get("tags","")+"]" if sw.get("tags") else ""
            pa_n=len(sw.get("post_actions",[]))
            pa_s=f" +{pa_n}⚡" if pa_n else ""
            item=QListWidgetItem(f"  {sw['name']}{tags}  [{sw.get('category','')}]{pa_s}  —  {sw.get('silent_args','')}")
            if ip and resolve_icon(ip): item.setIcon(QIcon(resolve_icon(ip)))
            item.setData(Qt.UserRole,sw); self.sw_list.addItem(item)
        self._refresh_cst()

    def _refresh_cst(self):
        self.cst_list.clear()
        for ct in CONFIG.data.get("custom_silent_types",[]):
            self.cst_list.addItem(f"  {ct['name']}  →  {ct['args']}")

    # ── CRUD: קטגוריות ────────────────────────────
    def _add_cat(self):
        d=CategoryEditDialog(parent=self)
        if d.exec_()==QDialog.Accepted:
            nd=d.get_data()
            if nd["name"]: CONFIG.data["categories"].append(nd); CONFIG.save(); self._refresh_all()
    def _edit_cat(self):
        item=self.cat_list.currentItem()
        if not item: return
        d=item.data(Qt.UserRole); dlg=CategoryEditDialog(cat_data=d,parent=self)
        if dlg.exec_()==QDialog.Accepted:
            nd=dlg.get_data()
            idx=next((i for i,c in enumerate(CONFIG.data["categories"]) if c["id"]==d["id"]),-1)
            if idx>=0: CONFIG.data["categories"][idx]=nd; CONFIG.save(); self._refresh_all()
    def _del_cats(self):
        items=self.cat_list.selectedItems()
        if not items: return
        ids={i.data(Qt.UserRole)["id"] for i in items}
        names=", ".join(i.data(Qt.UserRole)["name"] for i in items)
        if show_question(self,"מחיקה",f"למחוק {len(ids)} קטגוריות?\n{names}",
                                QMessageBox.Yes|QMessageBox.No)==QMessageBox.Yes:
            CONFIG.data["categories"]=[c for c in CONFIG.data["categories"] if c["id"] not in ids]
            CONFIG.save(); self._refresh_all()
    def _cat_up(self):
        r=self.cat_list.currentRow()
        if r>0:
            CONFIG.data["categories"].insert(r-1,CONFIG.data["categories"].pop(r))
            CONFIG.save(); self._refresh_all(); self.cat_list.setCurrentRow(r-1)
    def _cat_dn(self):
        r=self.cat_list.currentRow(); cats=CONFIG.data["categories"]
        if r<len(cats)-1:
            cats.insert(r+1,cats.pop(r)); CONFIG.save(); self._refresh_all(); self.cat_list.setCurrentRow(r+1)

    # ── CRUD: תוכנות ──────────────────────────────
    def _add_sw(self):
        dlg=SoftwareEditDialog(categories=CONFIG.data["categories"],parent=self)
        if dlg.exec_()==QDialog.Accepted:
            CONFIG.data["software"].append(dlg.get_data()); CONFIG.save(); self._refresh_all()
    def _add_multi_sw(self):
        paths,_=QFileDialog.getOpenFileNames(self,"בחר קבצים",SOFTWARE_DIR,
                                             "קבצי התקנה (*.exe *.msi *.bat *.cmd);;כל הקבצים (*)")
        if not paths: return
        cats=CONFIG.data["categories"]; added=0
        prog=QProgressDialog("מוסיף...","בטל",0,len(paths),self); prog.setMinimumDuration(0)
        for i,p in enumerate(paths):
            if prog.wasCanceled(): break
            prog.setValue(i); prog.setLabelText(os.path.basename(p)); QApplication.processEvents()
            stype,sargs=detect_silent_type(p); icon=extract_icon_from_exe(p)
            rel=CONFIG.make_relative(p)
            CONFIG.data["software"].append({
                "id":str(datetime.datetime.now().timestamp())+str(added),
                "name":os.path.splitext(os.path.basename(p))[0],"tags":"","description":"",
                "file":rel,"force_absolute":False,
                "category":cats[0]["name"] if cats else "",
                "silent_type":stype,"silent_args":sargs,"icon":icon,"post_actions":[],
                "auto_shortcut":False,"shortcut_path":""})
            added+=1
        prog.setValue(len(paths)); CONFIG.save(); self._refresh_all()
        show_info(self, "הוספה",f"נוספו {added} תוכנות.")
    def _edit_sw(self):
        item=self.sw_list.currentItem()
        if not item: return
        d=item.data(Qt.UserRole); dlg=SoftwareEditDialog(sw_data=d,categories=CONFIG.data["categories"],parent=self)
        if dlg.exec_()==QDialog.Accepted:
            nd=dlg.get_data()
            idx=next((i for i,s in enumerate(CONFIG.data["software"]) if s["id"]==d["id"]),-1)
            if idx>=0: CONFIG.data["software"][idx]=nd; CONFIG.save(); self._refresh_all()
    def _del_sws(self):
        items=self.sw_list.selectedItems()
        if not items: return
        ids={i.data(Qt.UserRole)["id"] for i in items}
        names=", ".join(i.data(Qt.UserRole)["name"] for i in items)
        if show_question(self,"מחיקה",f"למחוק {len(ids)} תוכנות?\n{names}",
                                QMessageBox.Yes|QMessageBox.No)==QMessageBox.Yes:
            CONFIG.data["software"]=[s for s in CONFIG.data["software"] if s["id"] not in ids]
            CONFIG.save(); self._refresh_all()
    def _sw_up(self):
        r=self.sw_list.currentRow()
        if r>0:
            CONFIG.data["software"].insert(r-1,CONFIG.data["software"].pop(r))
            CONFIG.save(); self._refresh_all(); self.sw_list.setCurrentRow(r-1)
    def _sw_dn(self):
        r=self.sw_list.currentRow(); sws=CONFIG.data["software"]
        if r<len(sws)-1:
            sws.insert(r+1,sws.pop(r)); CONFIG.save(); self._refresh_all(); self.sw_list.setCurrentRow(r+1)

    # ── סוגי התקנה שקטה מותאמים ───────────────────
    def _add_cst(self):
        d=CustomSilentTypeDialog(parent=self)
        if d.exec_()==QDialog.Accepted:
            CONFIG.data["custom_silent_types"].append(d.get_data()); CONFIG.save(); self._refresh_cst()
    def _edit_cst(self):
        r=self.cst_list.currentRow(); cts=CONFIG.data.get("custom_silent_types",[])
        if r<0 or r>=len(cts): return
        d=CustomSilentTypeDialog(data=cts[r],parent=self)
        if d.exec_()==QDialog.Accepted:
            cts[r]=d.get_data(); CONFIG.save(); self._refresh_cst()
    def _del_cst(self):
        r=self.cst_list.currentRow(); cts=CONFIG.data.get("custom_silent_types",[])
        if r<0 or r>=len(cts): return
        if show_question(self,"מחיקה",f"למחוק '{cts[r]['name']}'?",
                                QMessageBox.Yes|QMessageBox.No)==QMessageBox.Yes:
            cts.pop(r); CONFIG.save(); self._refresh_cst()

    # ── ייצוא / ייבוא ─────────────────────────────
    def _export_sw(self):
        path,_=QFileDialog.getSaveFileName(self,"ייצא",BASE_DIR,"JSON (*.json)")
        if not path: return
        data={"categories":CONFIG.data.get("categories",[]),"software":CONFIG.data.get("software",[]),
              "custom_silent_types":CONFIG.data.get("custom_silent_types",[]),
              "exported_at":datetime.datetime.now().isoformat(),"version":"5.0"}
        with open(path,"w",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False,indent=2)
        show_info(self, "ייצוא",f"✅ יוצא:\n{path}\n\n⚠️ תיקיית software\\ חייבת להישאר ללא שינוי!")
    def _import_sw(self):
        path,_=QFileDialog.getOpenFileName(self,"ייבא",BASE_DIR,"JSON (*.json)")
        if not path: return
        try:
            with open(path,"r",encoding="utf-8") as f: data=json.load(f)
        except Exception as e:
            QMessageBox.critical(self,"שגיאה",f"לא ניתן לקרוא:\n{e}"); return
        cats=data.get("categories",[]); sws=data.get("software",[]); cts=data.get("custom_silent_types",[])
        if show_question(self,"ייבוא",f"נמצאו:\n• {len(cats)} קטגוריות\n• {len(sws)} תוכנות\n• {len(cts)} סוגי שקטה\n\nהחלף הנוכחי?",
                                QMessageBox.Yes|QMessageBox.No)==QMessageBox.Yes:
            CONFIG.data["categories"]=cats; CONFIG.data["software"]=sws
            CONFIG.data["custom_silent_types"]=cts; CONFIG.save(); self._refresh_all()
            show_info(self, "ייבוא","✅ יובא בהצלחה!\n\n⚠️ ודא שתיקיית software\\ מכילה את הקבצים.")

    # ── סיסמאות ───────────────────────────────────
    def _pw_s(self,k): return "🔒 מוגדרת" if CONFIG.data.get(k) else "🔓 ללא"
    def _clr_pw(self,k):
        n="כלי" if k=="tool_password" else "הגדרות"
        if show_question(self,"מחיקה",f"למחוק סיסמת ה{n}?",
                                QMessageBox.Yes|QMessageBox.No)==QMessageBox.Yes:
            CONFIG.clear_password(k)
            self.tpw_lbl.setText(self._pw_s("tool_password"))
            self.spw_lbl.setText(self._pw_s("settings_password"))
    def _save_passwords(self):
        if self.tool_pw.text(): CONFIG.set_password("tool_password",self.tool_pw.text())
        if self.sets_pw.text(): CONFIG.set_password("settings_password",self.sets_pw.text())
        self.tool_pw.clear(); self.sets_pw.clear()
        self.tpw_lbl.setText(self._pw_s("tool_password")); self.spw_lbl.setText(self._pw_s("settings_password"))
        show_info(self, "שמירה","הסיסמאות נשמרו.")

    def _save_and_close(self):
        new_lang="he" if self.lang_he.isChecked() else "en"
        if new_lang!=CONFIG.data.get("language","he"):
            CONFIG.data["language"]=new_lang; CONFIG.save()
            show_info(self, "שפה","⚠️ שינוי השפה ייכנס לתוקף בהפעלה הבאה של הכלי.")
        else:
            CONFIG.save()
        self.accept()


# ══════════════ Clock ══════════════
class ClockLabel(QLabel):
    def __init__(self,parent=None):
        super().__init__(parent); self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("font-size:13px;color:#2c3e50;font-weight:bold;")
        t=QTimer(self); t.timeout.connect(self._tick); t.start(1000); self._tick()
    def _tick(self): self.setText(datetime.datetime.now().strftime("📅 %d/%m/%Y   🕐 %H:%M:%S"))

# ══════════════ InstallWorker ══════════════
class InstallWorker(QThread):
    progress    =pyqtSignal(int,int)
    status      =pyqtSignal(str)
    sw_status   =pyqtSignal(str,str)
    need_manual =pyqtSignal(dict)
    finished_all=pyqtSignal(list)

    def __init__(self,sw_list,silent=True,show_post_actions=True):
        super().__init__()
        self.sw_list=sw_list; self.silent=silent; self.show_post=show_post_actions
        self._decs={}; self._evt=threading.Event(); self.report=[]
        self._stop_requested=False

    def request_stop(self):
        """בקשת עצירת ההתקנה לאחר התוכנה הנוכחית"""
        self._stop_requested=True
        self._evt.set()  # שחרר המתנה ידנית אם קיימת

    def run(self):
        total=len(self.sw_list); done=0; queue=[]
        for sw in self.sw_list:
            if self._stop_requested: break
            sid=sw["id"]; fp=CONFIG.resolve_file(sw.get("file",""))
            if not os.path.exists(fp):
                self.sw_status.emit(sid,"error:קובץ לא נמצא")
                self.report.append({"sw":sw,"result":"error","msg":"קובץ לא נמצא"})
                done+=1; self.progress.emit(done,total); continue
            sa=sw.get("silent_args","").strip()
            # התקנה רגילה — רץ ללא ארגומנטים
            args=sa if self.silent else ""
            if self.silent and not sa: queue.append(sw); continue
            self.sw_status.emit(sid,"installing"); self.status.emit(f"מתקין: {sw['name']}...")
            rc=self._run(fp,args)
            done+=1; self.progress.emit(done,total)
            if rc in (0,3010):
                self.sw_status.emit(sid,"done")
                self.report.append({"sw":sw,"result":"success","msg":"" if rc==0 else "קוד 3010"})
                self._run_post_actions(sw,sid)
                self._handle_shortcut(sw)
            else:
                self.sw_status.emit(sid,f"error:קוד {rc}")
                self.report.append({"sw":sw,"result":"error","msg":f"קוד: {rc}"})
        # queue — תוכנות ללא args שקטים
        for sw in queue:
            if self._stop_requested: break
            sid=sw["id"]; fp=CONFIG.resolve_file(sw.get("file",""))
            self.sw_status.emit(sid,"installing"); self.status.emit(f"מנסה /S: {sw['name']}...")
            rc=self._run(fp,"/S")
            if rc in (0,3010):
                done+=1; self.progress.emit(done,total); self.sw_status.emit(sid,"done")
                self.report.append({"sw":sw,"result":"success","msg":"ברירת מחדל /S"})
                self._run_post_actions(sw,sid)
                self._handle_shortcut(sw)
            else:
                self._evt.clear(); self.need_manual.emit(sw); self._evt.wait(300)
                dec=self._decs.get(sid,"skip")
                if dec=="manual":
                    self._run(fp,""); self.sw_status.emit(sid,"manual")
                    self.report.append({"sw":sw,"result":"manual","msg":"ידני"})
                    self._run_post_actions(sw,sid)
                    self._handle_shortcut(sw)
                else:
                    self.sw_status.emit(sid,"skipped")
                    self.report.append({"sw":sw,"result":"skipped","msg":"דולג"})
                done+=1; self.progress.emit(done,total)
        clear_session(); self.finished_all.emit(self.report)

    def _run(self,fp,args):
        cmd=["msiexec","/i",fp]+(args.split() if args else []) if fp.lower().endswith(".msi") else [fp]+(args.split() if args else [])
        try: return subprocess.run(cmd,timeout=600).returncode
        except: return -1

    def _run_post_actions(self,sw,sid):
        """מריץ פעולות לאחר ההתקנה"""
        for a in sw.get("post_actions",[]):
            typ=a.get("type","exe"); cmd_s=a.get("cmd",""); args_s=a.get("args","")
            desc=a.get("desc","") or cmd_s; show=a.get("show_in_status",True)
            if not cmd_s: continue
            if show: self.status.emit(f"⚡ {desc}")
            try:
                if typ=="cmd":
                    full_cmd=f'cmd /c "{cmd_s}" {args_s}'.strip()
                    subprocess.run(full_cmd,shell=True,timeout=120,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    fp2=CONFIG.resolve_file(cmd_s)
                    c=[fp2]+(args_s.split() if args_s else [])
                    subprocess.run(c,timeout=300)
            except Exception as e:
                if show: self.status.emit(f"⚠️ {desc}: {e}")

    def _handle_shortcut(self,sw):
        """לאחר התקנה שקטה מוצלחת — מאתר (או יוצר) קיצור דרך בשולחן העבודה ושומר את הנתיב"""
        if not sw.get("auto_shortcut"): return
        sid=sw["id"]; name=sw["name"]
        self.status.emit(f"🔗 מאתר קיצור דרך: {name}...")
        import time; time.sleep(1.5)  # תן לתהליך ההתקנה להשלים יצירת קיצורי דרך
        path=sw.get("shortcut_path","").strip()
        # אם כבר יש נתיב שמור ועדיין קיים — אין צורך לחפש שוב
        if path and os.path.exists(path):
            return
        # חיפוש קיצור דרך קיים בשולחן העבודה
        lnk=find_desktop_shortcut(name)
        if lnk:
            self._persist_shortcut_path(sid,lnk)
            return
        # ניסיון נוסף — אתר EXE מותקן וצור קיצור דרך ידנית
        exe=find_installed_exe(name)
        if exe:
            try:
                from win32com.client import Dispatch
                desktop=os.path.join(os.environ.get("USERPROFILE",""),"Desktop")
                lnk_path=os.path.join(desktop,name+".lnk")
                sh=Dispatch('WScript.Shell'); shortcut=sh.CreateShortCut(lnk_path)
                shortcut.TargetPath=exe; shortcut.IconLocation=exe; shortcut.save()
                self._persist_shortcut_path(sid,lnk_path)
            except: pass

    def _persist_shortcut_path(self,sid,path):
        """שומר את נתיב קיצור הדרך שאותר חזרה ל-config, כדי שיוצג בפעם הבאה"""
        for s in CONFIG.data.get("software",[]):
            if s["id"]==sid:
                s["shortcut_path"]=path; CONFIG.save(); break

    def set_manual_decision(self,sid,dec): self._decs[sid]=dec; self._evt.set()

# ══════════════ SoftwareRowWidget ══════════════
class SoftwareRowWidget(QWidget):
    install_single=pyqtSignal(dict)
    def __init__(self,sw,is_installed=False,parent=None):
        super().__init__(parent); self.sw=sw; self.is_inst=is_installed; self._build_ui()

    def _build_ui(self):
        ip=self.sw.get("icon","")
        ml=QVBoxLayout(self); ml.setContentsMargins(0,0,0,0); ml.setSpacing(0)

        # ── שורה ראשית (תמיד גלויה) ──────────────────────────
        row=QWidget()
        row.setStyleSheet("background:white;border:none;")
        row.setMinimumHeight(38)
        rl=QHBoxLayout(row); rl.setContentsMargins(8,5,8,5); rl.setSpacing(8)

        # חץ פתיחה
        self.dbtn=QPushButton("▶"); self.dbtn.setFixedSize(20,20)
        self.dbtn.setStyleSheet("background:#f0f4f8;border:none;border-radius:4px;font-size:9px;color:#7f8c8d;"
                                "QPushButton:hover{background:#dde3ea;}")
        self.dbtn.clicked.connect(self._toggle)

        # תיבת סימון
        self.cb=QCheckBox()
        if self.is_inst: self.cb.setStyleSheet("color:#27ae60;")

        # אייקון (24×24)
        il=QLabel(); il.setFixedSize(24,24); il.setScaledContents(True)
        rip=resolve_icon(ip)
        if rip:
            il.setPixmap(QPixmap(rip).scaled(24,24,Qt.KeepAspectRatio,Qt.SmoothTransformation))

        # שם התוכנה (מודגש)
        nl=QLabel(self.sw["name"])
        nl.setStyleSheet("font-weight:bold;color:#27ae60;font-size:12px;" if self.is_inst
                         else "font-weight:bold;font-size:12px;")

        # פרטים טכניים (באותה שורה, אחרי השם)
        tech=self.sw.get("tech_info","")
        if tech:
            tech_lbl=QLabel(parse_tech_html(tech))
            tech_lbl.setTextFormat(Qt.RichText)
            tech_lbl.setStyleSheet("font-size:11px;margin-right:6px;")
        else:
            tech_lbl=QLabel("")

        # תגיות
        tags=self.sw.get("tags","")
        tags_lbl=QLabel(f"🏷️ {tags}" if tags else "")
        tags_lbl.setStyleSheet("color:#95a5a6;font-size:10px;margin-right:6px;")

        # סטטוס (מותקן / ⏳ וכו')
        self.slbl=QLabel(TR("installed_mark") if self.is_inst else "")
        self.slbl.setStyleSheet("color:#27ae60;font-size:11px;" if self.is_inst else "font-size:11px;")
        self.slbl.setMinimumWidth(110)

        # כפתור התקן
        self.ibtn=QPushButton(TR("install_btn")); self.ibtn.setFixedHeight(26)
        self.ibtn.setStyleSheet(
            "QPushButton{background:#2980b9;color:white;border-radius:5px;font-size:11px;padding:0 10px;border:none;}"
            "QPushButton:hover{background:#3498db;}QPushButton:disabled{background:#bdc3c7;}")
        self.ibtn.clicked.connect(lambda:self.install_single.emit(self.sw))

        for w2 in [self.dbtn,self.cb,il,nl,tech_lbl,tags_lbl]: rl.addWidget(w2)
        rl.addStretch()
        rl.addWidget(self.slbl); rl.addWidget(self.ibtn)
        ml.addWidget(row)

        # ── שורת פרטים (נפתחת ב-▶) ───────────────────────────
        self.dw=QWidget()
        self.dw.setStyleSheet("background:#f8fafc;border:none;border-top:1px solid #f0f2f5;")
        dl=QHBoxLayout(self.dw); dl.setContentsMargins(52,4,8,4); dl.setSpacing(8)

        # תיאור
        desc=self.sw.get("description","")
        if desc:
            desc_lbl=QLabel(desc); desc_lbl.setStyleSheet("color:#555;font-size:11px;")
            desc_lbl.setWordWrap(True); dl.addWidget(desc_lbl,1)
        else:
            dl.addStretch(1)

        # סימון קיצור דרך פעיל
        if self.sw.get("auto_shortcut"):
            sc_path=self.sw.get("shortcut_path","")
            sc_txt="🔗 קיצור דרך: " + (os.path.basename(sc_path) if sc_path else "יזוהה אוטומטית")
            sc_lbl=QLabel(sc_txt); sc_lbl.setStyleSheet("color:#16a085;font-size:10px;")
            dl.addWidget(sc_lbl,0,Qt.AlignVCenter)

        # כפתור אודות בסוף השורה (ממורכז אנכית)
        about_text=self.sw.get("about_text",""); source_url=self.sw.get("source_url","")
        if about_text or source_url:
            ab_btn=QPushButton("ℹ️ אודות"); ab_btn.setFixedHeight(26)
            ab_btn.setStyleSheet(
                "QPushButton{background:#7f8c8d;color:white;border-radius:4px;font-size:10px;padding:0 8px;}"
                "QPushButton:hover{background:#95a5a6;}")
            sw_ref=self.sw
            ab_btn.clicked.connect(lambda checked=False,s=sw_ref:self._show_about(s))
            dl.addWidget(ab_btn,0,Qt.AlignVCenter)

        self.dw.setVisible(False); ml.addWidget(self.dw)

        # מפריד עדין (1px, כמעט בלתי נראה)
        sep=QWidget(); sep.setFixedHeight(1)
        sep.setStyleSheet("background:#f0f2f5;margin:0;"); ml.addWidget(sep)

    def _toggle(self):
        v=self.dw.isVisible(); self.dw.setVisible(not v); self.dbtn.setText("▼" if not v else "▶")

    def set_detail_visible(self,visible):
        """קובע את מצב פתיחת פאנל התיאור (משמש להרחב/כווץ תיאור גלובלי)"""
        self.dw.setVisible(visible); self.dbtn.setText("▼" if visible else "▶")

    def _show_about(self,sw):
        dlg=QDialog(self); dlg.setWindowTitle(f"אודות — {sw['name']}")
        dlg.setLayoutDirection(get_dir()); dlg.setMinimumWidth(420)
        lay=QVBoxLayout(dlg)
        # אייקון + שם
        top=QHBoxLayout()
        ip=sw.get("icon","")
        rip=resolve_icon(ip)
        if rip:
            ico=QLabel(); ico.setFixedSize(48,48)
            ico.setPixmap(QPixmap(rip).scaled(48,48,Qt.KeepAspectRatio,Qt.SmoothTransformation))
            top.addWidget(ico)
        nm=QLabel(f"<b style='font-size:14px;'>{sw['name']}</b>")
        nm.setTextFormat(Qt.RichText); top.addWidget(nm); top.addStretch()
        lay.addLayout(top)
        # פרטים טכניים
        tech=sw.get("tech_info","")
        if tech:
            tl=QLabel(parse_tech_html(tech)); tl.setTextFormat(Qt.RichText); lay.addWidget(tl)
        sep=QWidget(); sep.setFixedHeight(1); sep.setStyleSheet("background:#dde;"); lay.addWidget(sep)
        # טקסט אודות
        about=sw.get("about_text","")
        if about:
            atxt=QTextEdit(); atxt.setReadOnly(True); atxt.setPlainText(about)
            atxt.setMaximumHeight(120); lay.addWidget(atxt)
        # קישור מקור
        url=sw.get("source_url","")
        if url:
            url_btn=QPushButton(f"🌐 פתח מקור: {url}")
            url_btn.setStyleSheet("color:#2980b9;text-decoration:underline;background:transparent;border:none;")
            url_btn.clicked.connect(lambda:QDesktopServices.openUrl(QUrl(url)))
            lay.addWidget(url_btn)
        close=QPushButton("סגור"); close.clicked.connect(dlg.accept); lay.addWidget(close,alignment=Qt.AlignLeft)
        dlg.exec_()

    def set_status(self,status):
        icons={"installing":TR("installing"),"done":TR("done"),"error":TR("error"),"skipped":TR("skipped"),"manual":TR("manual")}
        color={"installing":"#e67e22","done":"#27ae60","error":"#e74c3c","skipped":"#95a5a6","manual":"#3498db"}
        key=status.split(":")[0]; lbl=icons.get(key,status)
        if ":" in status: lbl+=" — "+status.split(":",1)[1]
        self.slbl.setText(lbl); self.slbl.setStyleSheet(f"font-size:11px;color:{color.get(key,'#333')};")
        self.ibtn.setEnabled(key!="installing")
    def set_install_enabled(self,e): self.ibtn.setEnabled(e)


# ══════════════ CategoryWidget ══════════════
class CategoryWidget(QWidget):
    install_single_sw=pyqtSignal(dict)
    def __init__(self,cat,sw_list,inst_names=None,parent=None):
        super().__init__(parent); self.cat=cat; self.sw_list=sw_list
        self.inst_names=inst_names or set(); self.sw_widgets=[]; self._build_ui()

    def _build_ui(self):
        ml=QVBoxLayout(self); ml.setContentsMargins(0,0,0,6); ml.setSpacing(0)
        hdr=QWidget()
        hdr.setStyleSheet("background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #2c3e50,stop:1 #34495e);"
                          "border-radius:8px;")
        hdr.setMinimumHeight(38)
        hl=QHBoxLayout(hdr); hl.setContentsMargins(10,5,10,5)
        self.cbtn=QPushButton("▼"); self.cbtn.setFixedSize(24,24)
        self.cbtn.setStyleSheet("background:rgba(255,255,255,0.15);color:white;border:none;border-radius:4px;font-size:11px;")
        self.cbtn.clicked.connect(self._toggle)
        self.chk=QCheckBox(); self.chk.setStyleSheet("color:white;"); self.chk.stateChanged.connect(self._toggle_all)
        cl=QLabel(f"📂 {self.cat['name']}"); cl.setStyleSheet("color:white;font-weight:bold;font-size:13px;")
        dl=QLabel(self.cat.get("description","")); dl.setStyleSheet("color:#a9b7c6;font-size:11px;margin-right:8px;")
        ct_badge=QLabel(f" {len(self.sw_list)} ")
        ct_badge.setStyleSheet("background:rgba(46,204,113,0.8);color:white;font-size:10px;"
                               "border-radius:8px;padding:1px 5px;font-weight:bold;")
        for w2 in [self.cbtn,self.chk,cl,dl,ct_badge]: hl.addWidget(w2)
        hl.addStretch(); ml.addWidget(hdr)
        self.content=QWidget()
        self.content.setStyleSheet("background:white;border:1px solid #e0e4e8;border-top:none;"
                                   "border-radius:0 0 8px 8px;")
        cl2=QVBoxLayout(self.content); cl2.setContentsMargins(18,4,4,4); cl2.setSpacing(0)
        for sw in self.sw_list:
            w2=SoftwareRowWidget(sw,sw["name"].lower() in self.inst_names)
            w2.install_single.connect(self.install_single_sw); self.sw_widgets.append(w2); cl2.addWidget(w2)
        ml.addWidget(self.content)

    def _toggle(self):
        v=self.content.isVisible(); self.content.setVisible(not v); self.cbtn.setText("▶" if v else "▼")
    def _toggle_all(self,s):
        for w2 in self.sw_widgets: w2.cb.setChecked(s==Qt.Checked)
    def get_selected(self): return [w2.sw for w2 in self.sw_widgets if w2.cb.isChecked()]
    def set_sw_status(self,sid,st):
        for w2 in self.sw_widgets:
            if w2.sw["id"]==sid: w2.set_status(st)
    def set_install_enabled(self,e):
        for w2 in self.sw_widgets: w2.set_install_enabled(e)
    def set_descriptions_expanded(self,expand):
        for w2 in self.sw_widgets: w2.set_detail_visible(expand)

# ══════════════ InstalledScanDialog ══════════════
class InstalledScanDialog(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent)
        lbl="Installed Software" if CONFIG.data.get("language","he")=="en" else "תוכנות מותקנות"
        self.setWindowTitle(lbl); self.setLayoutDirection(get_dir()); self.setMinimumSize(920,620)
        self.sw_list=[]; self._build_ui(); self._scan()

    def _build_ui(self):
        lay=QVBoxLayout(self)
        top=QHBoxLayout()
        self.search=QLineEdit(); self.search.setPlaceholderText("🔍 חיפוש..."); self.search.textChanged.connect(self._filter)
        self.cat_cb=QComboBox(); self.cat_cb.addItem("הכל"); self.cat_cb.currentTextChanged.connect(self._filter)
        top.addWidget(self.search); top.addWidget(self.cat_cb); lay.addLayout(top)
        self.tbl=QTableWidget(0,5); self.tbl.setHorizontalHeaderLabels(["שם","מפרסם","גרסה","תאריך","קטגוריה"])
        self.tbl.horizontalHeader().setStretchLastSection(True)
        self.tbl.setSelectionBehavior(QTableWidget.SelectRows); self.tbl.setSortingEnabled(True)
        self.tbl.setAlternatingRowColors(True); self.tbl.setLayoutDirection(get_dir()); lay.addWidget(self.tbl)
        br=QHBoxLayout()
        for lbl2,fn in [("📁 קיצורי דרך",self._shortcuts),("📄 HTML",lambda:self._export("html")),
                         ("📄 טקסט",lambda:self._export("txt")),("🔄 רענן",self._scan)]:
            b=QPushButton(lbl2); b.clicked.connect(fn); br.addWidget(b)
        br.addStretch(); lay.addLayout(br)
        self.lbl=QLabel("סורק..."); self.lbl.setStyleSheet("color:#666;"); lay.addWidget(self.lbl)

    def _scan(self):
        self.lbl.setText("⏳ סורק..."); QApplication.processEvents()
        self.sw_list=get_installed_software()
        cats=sorted(set(s["category"] for s in self.sw_list))
        self.cat_cb.blockSignals(True); self.cat_cb.clear(); self.cat_cb.addItem("הכל")
        self.cat_cb.addItems(cats); self.cat_cb.blockSignals(False)
        self._populate(self.sw_list); self.lbl.setText(f"✅ נמצאו {len(self.sw_list)} תוכנות")

    def _populate(self,items):
        self.tbl.setSortingEnabled(False); self.tbl.setRowCount(len(items))
        for r,s in enumerate(items):
            for c2,k in enumerate(["name","publisher","version","install_date","category"]):
                self.tbl.setItem(r,c2,QTableWidgetItem(s.get(k,"")))
        self.tbl.setSortingEnabled(True); self.tbl.resizeColumnsToContents()

    def _filter(self):
        t=self.search.text().lower(); cat=self.cat_cb.currentText()
        self._populate([s for s in self.sw_list
                        if (t in s["name"].lower() or t in s.get("publisher","").lower())
                        and (cat=="הכל" or s["category"]==cat)])

    def _shortcuts(self):
        """יוצר קיצורי דרך לתוכנות מותקנות לפי DisplayIcon ברגיסטר"""
        dest=QFileDialog.getExistingDirectory(self,"יעד",os.path.expanduser("~\\Desktop"))
        if not dest: return
        by_cat=show_question(self,"מיון","מיון לפי קטגוריות?",QMessageBox.Yes|QMessageBox.No)
        created=0; skipped=[]
        for s in self.sw_list:
            # נסה DisplayIcon מהרגיסטר
            raw_icon=s.get("icon","")
            tgt=raw_icon.split(",")[0].strip('"').strip() if raw_icon else ""
            # נסה גם find_installed_exe אם אין
            if not tgt or not os.path.isfile(tgt):
                tgt=find_installed_exe(s["name"])
            if not tgt or not os.path.isfile(tgt):
                skipped.append(s["name"]); continue
            d=os.path.join(dest,s["category"]) if by_cat==QMessageBox.Yes else dest
            os.makedirs(d,exist_ok=True)
            try:
                from win32com.client import Dispatch
                sh=Dispatch('WScript.Shell'); lnk=sh.CreateShortCut(os.path.join(d,s["name"]+".lnk"))
                lnk.TargetPath=tgt; lnk.save(); created+=1
            except: skipped.append(s["name"])
        msg=f"נוצרו {created} קיצורי דרך."
        if skipped: msg+=f"\n\nלא נמצאו ({len(skipped)}):\n"+"\n".join(f"• {n}" for n in skipped[:10])
        show_info(self, "סיום",msg)

    def _export(self,fmt):
        ext="HTML (*.html)" if fmt=="html" else "טקסט (*.txt)"
        path,_=QFileDialog.getSaveFileName(self,"שמור",REPORTS_DIR,ext)
        if not path: return
        if fmt=="html":
            rows="".join(f"<tr><td>{s['name']}</td><td>{s.get('publisher','')}</td>"
                         f"<td>{s.get('version','')}</td><td>{s.get('install_date','')}</td>"
                         f"<td>{s.get('category','')}</td></tr>" for s in self.sw_list)
            html=(f'<!DOCTYPE html><html dir="rtl"><head><meta charset="UTF-8"><title>דו"ח</title>'
                  f'<style>body{{font-family:Arial;direction:rtl;padding:20px;}}'
                  f'th{{background:#2c3e50;color:white;padding:8px;text-align:right;}}'
                  f'td{{padding:6px;border-bottom:1px solid #eee;}}table{{border-collapse:collapse;width:100%;}}</style></head><body>'
                  f'<h2>דו"ח — {datetime.datetime.now().strftime("%d/%m/%Y %H:%M")} | סה"כ: {len(self.sw_list)}</h2>'
                  f'<table><tr><th>שם</th><th>מפרסם</th><th>גרסה</th><th>תאריך</th><th>קטגוריה</th></tr>{rows}</table></body></html>')
            open(path,"w",encoding="utf-8").write(html)
        else:
            lines=[f'דו"ח — {datetime.datetime.now().strftime("%d/%m/%Y %H:%M")}','='*70]
            lines+=[f"{s['name']} | {s.get('publisher','')} | {s.get('version','')} | {s.get('category','')}" for s in self.sw_list]
            open(path,"w",encoding="utf-8").write("\n".join(lines))
        os.startfile(path)

# ══════════════ AlreadyInstalledDialog ══════════════
class AlreadyInstalledDialog(QDialog):
    def __init__(self,sw_list,parent=None):
        super().__init__(parent); self.setWindowTitle("תוכנות מותקנות — בחר להחליף")
        self.setLayoutDirection(get_dir()); self.setMinimumWidth(520)
        lay=QVBoxLayout(self); lay.addWidget(QLabel("התוכנות הבאות כבר מותקנות. סמן אלה להחליף:"))
        self.cbs={}
        for sw in sw_list:
            cb=QCheckBox(sw["name"]); self.cbs[sw["id"]]=cb; lay.addWidget(cb)
        row=QHBoxLayout()
        for lbl2,v in [("✅ סמן הכל",True),("☐ נקה הכל",False)]:
            b=QPushButton(lbl2); b.clicked.connect(lambda _,val=v:[c.setChecked(val) for c in self.cbs.values()])
            row.addWidget(b)
        row.addStretch(); lay.addLayout(row)
        btns=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject); lay.addWidget(btns)
    def get_skipped_ids(self): return [sid for sid,cb in self.cbs.items() if not cb.isChecked()]

# ══════════════ ReportDialog ══════════════
class ReportDialog(QDialog):
    def __init__(self,report,parent=None):
        super().__init__(parent); self.setWindowTitle(TR("report_title"))
        self.setLayoutDirection(get_dir()); self.setMinimumSize(700,520); self.report=report; self._build_ui()

    def _build_ui(self):
        lay=QVBoxLayout(self)
        suc=sum(1 for r in self.report if r["result"]=="success")
        err=sum(1 for r in self.report if r["result"]=="error")
        skp=sum(1 for r in self.report if r["result"]=="skipped")
        sl=QLabel(f"✅ {suc}   ❌ {err}   ⏭️ {skp}   📅 {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")
        sl.setStyleSheet("font-size:13px;font-weight:bold;color:#2c3e50;padding:6px;"); lay.addWidget(sl)
        tbl=QTableWidget(len(self.report),3); tbl.setHorizontalHeaderLabels(["תוכנה","תוצאה","הערה"])
        tbl.setLayoutDirection(get_dir()); tbl.setAlternatingRowColors(True)
        rm={"success":"✅ הצלחה","error":"❌ שגיאה","skipped":"⏭️ דולג","manual":"👤 ידני"}
        for r,item in enumerate(self.report):
            sw=item["sw"]; ni=QTableWidgetItem(sw["name"])
            ip=sw.get("icon","")
            if ip and resolve_icon(ip): ni.setIcon(QIcon(resolve_icon(ip)))
            tbl.setItem(r,0,ni)
            ri=QTableWidgetItem(rm.get(item["result"],item["result"]))
            ri.setForeground(QColor("#27ae60" if item["result"]=="success" else "#e74c3c" if item["result"]=="error" else "#666"))
            tbl.setItem(r,1,ri); tbl.setItem(r,2,QTableWidgetItem(item.get("msg","")))
        tbl.resizeColumnsToContents(); tbl.horizontalHeader().setStretchLastSection(True); lay.addWidget(tbl)
        br=QHBoxLayout()
        for lbl2,fn in [("📄 יצא HTML",self._export_html),("📁 קיצורי דרך",self._shortcuts)]:
            b=QPushButton(lbl2); b.clicked.connect(fn); br.addWidget(b)
        cl=QPushButton("סגור"); cl.clicked.connect(self.accept)
        br.addStretch(); br.addWidget(cl); lay.addLayout(br)

    def _shortcuts(self):
        dest=QFileDialog.getExistingDirectory(self,"יעד",os.path.expanduser("~\\Desktop"))
        if not dest: return
        ok=[i for i in self.report if i["result"] in ("success","manual")]
        created=0; nf=[]
        for item in ok:
            sw=item["sw"]; exe=find_installed_exe(sw["name"])
            if not exe: nf.append(sw["name"]); continue
            try:
                from win32com.client import Dispatch
                sh=Dispatch('WScript.Shell'); lnk=sh.CreateShortCut(os.path.join(dest,sw["name"]+".lnk"))
                lnk.TargetPath=exe
                ip=sw.get("icon",""); lnk.IconLocation=ip if ip and os.path.exists(ip) else exe
                lnk.save(); created+=1
            except Exception as e: nf.append(f"{sw['name']} ({e})")
        msg=f"נוצרו {created} קיצורי דרך."
        if nf: msg+="\n\nלא נמצאו:\n"+"\n".join(f"• {n}" for n in nf)
        show_info(self, "קיצורי דרך",msg)

    def _export_html(self):
        path,_=QFileDialog.getSaveFileName(self,"שמור",REPORTS_DIR,"HTML (*.html)")
        if not path: return
        rm={"success":"✅ הצלחה","error":"❌ שגיאה","skipped":"⏭️ דולג","manual":"👤 ידני"}
        rows=""
        for item in self.report:
            sw=item["sw"]; ih=""
            rip=resolve_icon(sw.get("icon",""))
            if rip:
                b64=base64.b64encode(open(rip,"rb").read()).decode()
                ext=os.path.splitext(rip)[1].lstrip(".") or "png"
                ih=f'<img src="data:image/{ext};base64,{b64}" width="22" height="22" style="vertical-align:middle;margin-left:4px;">'
            c="#27ae60" if item["result"]=="success" else "#e74c3c" if item["result"]=="error" else "#666"
            rows+=f'<tr><td>{ih}{sw["name"]}</td><td>{sw.get("description","")}</td><td style="color:{c};font-weight:bold;">{rm.get(item["result"],item["result"])}</td><td>{item.get("msg","")}</td></tr>\n'
        suc=sum(1 for r in self.report if r["result"]=="success")
        html=(f'<!DOCTYPE html><html dir="rtl"><head><meta charset="UTF-8"><title>דו"ח</title>'
              f'<style>body{{font-family:Arial;direction:rtl;background:#f9f9f9;padding:20px;}}'
              f'h2{{color:#2c3e50;}} table{{border-collapse:collapse;width:100%;background:white;}}'
              f'th{{background:#2c3e50;color:white;padding:10px;text-align:right;}}'
              f'td{{padding:8px;border-bottom:1px solid #eee;}} tr:hover{{background:#f0f7ff;}}</style>'
              f'</head><body>'
              f'<h2>📋 {TR("report_title")} — {datetime.datetime.now().strftime("%d/%m/%Y %H:%M")}</h2>'
              f'<p>✅ {suc} | סה"כ: {len(self.report)}</p>'
              f'<table><tr><th>תוכנה</th><th>תיאור</th><th>תוצאה</th><th>הערה</th></tr>{rows}</table></body></html>')
        open(path,"w",encoding="utf-8").write(html); os.startfile(path)


# ══════════════ SearchResultWidget ══════════════
class SearchResultWidget(QWidget):
    """תוצאות חיפוש — רשימה פשוטה ללא קטגוריות"""
    install_single_sw=pyqtSignal(dict)
    def __init__(self,sw_list,inst_names=None,parent=None):
        super().__init__(parent); self.sw_list=sw_list; self.inst_names=inst_names or set()
        self.sw_widgets=[]; self._build_ui()
    def _build_ui(self):
        ml=QVBoxLayout(self); ml.setContentsMargins(0,0,0,0); ml.setSpacing(0)
        hdr=QWidget(); hdr.setStyleSheet("background:#8e44ad;border-radius:6px;")
        hl=QHBoxLayout(hdr); hl.setContentsMargins(8,5,8,5)
        lbl=QLabel(f"🔍 תוצאות חיפוש ({len(self.sw_list)} תוכנות)")
        lbl.setStyleSheet("color:white;font-weight:bold;font-size:13px;"); hl.addWidget(lbl); hl.addStretch()
        ml.addWidget(hdr)
        cont=QWidget(); cont.setStyleSheet("background:white;border:1px solid #c39bd3;border-top:none;border-radius:0 0 4px 4px;")
        cl=QVBoxLayout(cont); cl.setContentsMargins(18,2,4,2); cl.setSpacing(0)
        for sw in self.sw_list:
            w2=SoftwareRowWidget(sw,sw["name"].lower() in self.inst_names)
            w2.install_single.connect(self.install_single_sw); self.sw_widgets.append(w2); cl.addWidget(w2)
        ml.addWidget(cont)
    def get_selected(self): return [w2.sw for w2 in self.sw_widgets if w2.cb.isChecked()]
    def set_install_enabled(self,e):
        for w2 in self.sw_widgets: w2.set_install_enabled(e)
    def set_sw_status(self,sid,st):
        for w2 in self.sw_widgets:
            if w2.sw["id"]==sid: w2.set_status(st)
    def set_descriptions_expanded(self,expand):
        for w2 in self.sw_widgets: w2.set_detail_visible(expand)

# ══════════════ MainWindow ══════════════
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"💿  {TR("app_name")}")
        self.setLayoutDirection(get_dir())
        self.setMinimumSize(1000,760)
        # שמור כפתורי חלון סטנדרטיים
        self.setWindowFlags(Qt.Window|Qt.WindowMinimizeButtonHint|Qt.WindowCloseButtonHint|Qt.WindowMaximizeButtonHint)
        self.cat_widgets=[]; self.search_widget=None; self.worker=None; self._last_report=[]
        self._search_mode=False
        self._build_ui(); self._refresh_main()
        self._check_resume_session()

    def _check_resume_session(self):
        """בדיקה אם יש session שלא הושלם"""
        sess=load_session()
        if not sess: return
        remaining_ids=sess.get("remaining",[])
        if not remaining_ids: clear_session(); return
        sw_map={s["id"]:s for s in CONFIG.data.get("software",[])}
        remaining=[sw_map[sid] for sid in remaining_ids if sid in sw_map]
        if not remaining: clear_session(); return
        names=", ".join(s["name"] for s in remaining[:3])
        if len(remaining)>3: names+=f" ו-{len(remaining)-3} נוספות"
        reply=show_question(self,"המשך התקנה",
            f"⚡ נמצאה התקנה שלא הושלמה:\n{names}\n\nהאם להמשיך?",
            QMessageBox.Yes|QMessageBox.No)
        if reply==QMessageBox.Yes:
            self._run_install(remaining)
        else:
            clear_session()

    def _build_ui(self):
        c=QWidget(); self.setCentralWidget(c)
        c.setStyleSheet("""
            QWidget { background: #f0f2f5; }
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical { background:#e8ecef; width:8px; border-radius:4px; }
            QScrollBar::handle:vertical { background:#bdc3c7; border-radius:4px; min-height:30px; }
            QScrollBar::handle:vertical:hover { background:#95a5a6; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
            QPushButton { border-radius:6px; padding:3px 10px; font-size:12px; }
        """)
        ml=QVBoxLayout(c); ml.setContentsMargins(12,10,12,12); ml.setSpacing(8)

        # ── כותרת עליונה (Header Bar) ──
        header=QWidget()
        header.setStyleSheet("background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #1a252f,stop:1 #2c3e50);"
                             "border-radius:10px;")
        header.setMinimumHeight(56)
        tr=QHBoxLayout(header); tr.setContentsMargins(14,8,14,8); tr.setSpacing(10)

        # לוגו + כותרת
        logo_lbl=QLabel()
        ico=get_app_icon()
        if not ico.isNull(): logo_lbl.setPixmap(ico.pixmap(36,36))
        tr.addWidget(logo_lbl)

        self.title_lbl=QLabel(TR("app_name"))
        self.title_lbl.setStyleSheet("font-size:18px;font-weight:bold;color:white;letter-spacing:0.5px;")
        tr.addWidget(self.title_lbl)
        tr.addStretch()

        self.clock=ClockLabel()
        self.clock.setStyleSheet("font-size:12px;color:#bdc3c7;font-weight:bold;")
        tr.addWidget(self.clock)
        tr.addSpacing(10)

        # חיפוש
        search_frame=QWidget()
        search_frame.setStyleSheet("background:rgba(255,255,255,0.12);border-radius:16px;")
        sf_lay=QHBoxLayout(search_frame); sf_lay.setContentsMargins(8,2,4,2); sf_lay.setSpacing(4)
        self.search_box=QLineEdit(); self.search_box.setPlaceholderText(TR("search_ph"))
        self.search_box.setMinimumWidth(180); self.search_box.setMaximumWidth(260)
        self.search_box.setStyleSheet("border:none;background:transparent;color:white;font-size:12px;"
                                      "QLineEdit::placeholder{color:#95a5a6;}")
        self.search_box.returnPressed.connect(self._do_search)
        self.search_go_btn=QPushButton("🔍"); self.search_go_btn.setFixedSize(24,24)
        self.search_go_btn.setStyleSheet("background:rgba(255,255,255,0.2);color:white;border-radius:12px;font-size:11px;border:none;")
        self.search_go_btn.clicked.connect(self._do_search)
        self.search_clear_btn=QPushButton("✖"); self.search_clear_btn.setFixedSize(24,24)
        self.search_clear_btn.setStyleSheet("background:#e74c3c;color:white;border-radius:12px;font-size:10px;border:none;")
        self.search_clear_btn.setVisible(False); self.search_clear_btn.clicked.connect(self._clear_search)
        sf_lay.addWidget(self.search_box); sf_lay.addWidget(self.search_go_btn); sf_lay.addWidget(self.search_clear_btn)
        tr.addWidget(search_frame)
        tr.addSpacing(6)

        # כפתורי פעולה עליונים
        for lbl2,fn,color in [(TR("refresh"),self._refresh_main,"#2980b9"),
                               (TR("scan"),self._open_scan,"#8e44ad"),
                               (TR("settings"),self._open_settings,"#2c3e50")]:
            b=QPushButton(lbl2); b.setMinimumHeight(32)
            b.setStyleSheet(f"QPushButton{{background:{color};color:white;border-radius:6px;font-size:12px;padding:0 10px;border:none;}}"
                            f"QPushButton:hover{{background:{color}cc;}}")
            b.clicked.connect(fn); tr.addWidget(b)
        ml.addWidget(header)

        # ── פקדי בחירה ──
        ctrl_frame=QWidget()
        ctrl_frame.setStyleSheet("background:white;border-radius:8px;border:1px solid #e0e4e8;")
        ctrl=QHBoxLayout(ctrl_frame); ctrl.setContentsMargins(10,6,10,6); ctrl.setSpacing(6)
        btn_configs=[
            ("expand_all","#3498db",lambda:self._expand_all(True)),
            ("collapse_all","#7f8c8d",lambda:self._expand_all(False)),
            ("expand_desc","#16a085",lambda:self._expand_all_descriptions(True)),
            ("collapse_desc","#95a5a6",lambda:self._expand_all_descriptions(False)),
            ("select_all","#27ae60",lambda:self._sel_all(True)),
            ("clear_all","#e74c3c",lambda:self._sel_all(False)),
        ]
        for key,color,fn in btn_configs:
            b=QPushButton(TR(key)); b.setFixedHeight(28)
            b.setStyleSheet(f"QPushButton{{background:{color};color:white;border-radius:5px;font-size:11px;padding:0 10px;border:none;}}"
                            f"QPushButton:hover{{background:{color}cc;}}")
            b.clicked.connect(fn)
            ctrl.addWidget(b)
        ctrl.addStretch(); ml.addWidget(ctrl_frame)

        # ── גלילה ──
        scroll=QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setLayoutDirection(get_dir()); scroll.setFrameShape(QFrame.NoFrame)
        self.sw_container=QWidget()
        self.sw_layout=QVBoxLayout(self.sw_container); self.sw_layout.setSpacing(6); self.sw_layout.addStretch()
        scroll.setWidget(self.sw_container); ml.addWidget(scroll,stretch=1)

        # ── אפשרויות ──
        opt_frame=QWidget()
        opt_frame.setStyleSheet("background:white;border-radius:8px;border:1px solid #e0e4e8;")
        opt=QHBoxLayout(opt_frame); opt.setContentsMargins(12,6,12,6); opt.setSpacing(14)
        self.sr=QRadioButton(TR("silent_install")); self.sr.setChecked(True)
        self.nr=QRadioButton(TR("normal_install"))
        self.nc=QCheckBox(TR("notify_on_done")); self.nc.setChecked(CONFIG.data.get("notify_on_complete",True))
        for w2 in [self.sr,self.nr]: opt.addWidget(w2)
        # זיהוי ארכיטקטורת המחשב
        arch_lbl=QLabel(ARCH_LABEL)
        arch_lbl.setStyleSheet("color:#7f8c8d;font-size:11px;padding:2px 8px;background:#f0f4f8;border-radius:4px;")
        opt.addWidget(arch_lbl)
        opt.addStretch(); opt.addWidget(self.nc); ml.addWidget(opt_frame)

        self.prog=QProgressBar(); self.prog.setVisible(False); self.prog.setMinimumHeight(22)
        self.prog.setStyleSheet("""
            QProgressBar{border:none;border-radius:11px;background:#e8ecef;text-align:center;font-size:11px;color:#2c3e50;}
            QProgressBar::chunk{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #27ae60,stop:1 #2ecc71);border-radius:11px;}
        """)
        ml.addWidget(self.prog)
        self.slbl=QLabel(TR("ready")); self.slbl.setStyleSheet("color:#555;font-size:12px;"); ml.addWidget(self.slbl)

        # ── שורת מידע על נבחרים ──
        sel_row=QHBoxLayout()
        self.sel_count_lbl=QLabel("לא נבחרו תוכנות")
        self.sel_count_lbl.setStyleSheet("color:#7f8c8d;font-size:12px;")
        self.sel_preview_btn=QPushButton("👁 הצג נבחרים")
        self.sel_preview_btn.setFixedHeight(28)
        self.sel_preview_btn.setStyleSheet(
            "QPushButton{background:#2980b9;color:white;border-radius:5px;font-size:11px;padding:0 10px;}"
            "QPushButton:hover{background:#3498db;}QPushButton:disabled{background:#bdc3c7;}")
        self.sel_preview_btn.setEnabled(False)
        self.sel_preview_btn.clicked.connect(self._show_selected_preview)
        sel_row.addWidget(self.sel_count_lbl); sel_row.addWidget(self.sel_preview_btn); sel_row.addStretch()
        ml.addLayout(sel_row)

        br=QHBoxLayout()
        self.ibtn=QPushButton(TR("install_selected")); self.ibtn.setMinimumHeight(44)
        self.ibtn.setStyleSheet("""QPushButton{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #2ecc71,stop:1 #27ae60);
            color:white;font-size:16px;font-weight:bold;border-radius:8px;border:none;}
            QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #58d68d,stop:1 #2ecc71);}
            QPushButton:pressed{background:#1e8449;}QPushButton:disabled{background:#95a5a6;}""")
        self.ibtn.clicked.connect(self._start_install)

        self.stop_btn=QPushButton("⏹ עצור התקנה"); self.stop_btn.setMinimumHeight(44)
        self.stop_btn.setStyleSheet("""QPushButton{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #e74c3c,stop:1 #c0392b);
            color:white;font-size:14px;font-weight:bold;border-radius:8px;border:none;}
            QPushButton:hover{background:#e74c3c;}QPushButton:pressed{background:#a93226;}""")
        self.stop_btn.setVisible(False)
        self.stop_btn.clicked.connect(self._stop_install)

        rb=QPushButton(TR("last_report")); rb.setMinimumHeight(44); rb.clicked.connect(self._show_last_report)
        rb.setStyleSheet("QPushButton{background:#34495e;color:white;font-size:13px;border-radius:8px;border:none;}"
                         "QPushButton:hover{background:#4a6278;}")
        br.addWidget(self.ibtn,stretch=1)
        br.addWidget(self.stop_btn)
        br.addWidget(rb)
        ml.addLayout(br)

        # טיימר לעדכון מספר נבחרים
        self._sel_timer=QTimer(self); self._sel_timer.timeout.connect(self._update_sel_count); self._sel_timer.start(400)

    # ── חיפוש ──────────────────────────────────────
    def _do_search(self):
        q=self.search_box.text().strip().lower()
        if not q: self._clear_search(); return
        all_sw=CONFIG.data.get("software",[])
        results=[sw for sw in all_sw
                 if q in sw["name"].lower()
                 or q in sw.get("tags","").lower()
                 or q in sw.get("description","").lower()]
        self._search_mode=True; self.search_clear_btn.setVisible(True)
        try: inst={s["name"].lower() for s in get_installed_software()}
        except: inst=set()
        self._clear_cat_widgets()
        if results:
            w2=SearchResultWidget(results,inst)
            w2.install_single_sw.connect(self._install_single)
            self.cat_widgets.append(w2); self.sw_layout.addWidget(w2)
        else:
            lbl=QLabel("לא נמצאו תוצאות."); lbl.setStyleSheet("color:#aaa;font-size:14px;padding:20px;")
            lbl.setAlignment(Qt.AlignCenter); self.sw_layout.addWidget(lbl); self.cat_widgets.append(lbl)
        self.sw_layout.addStretch()

    def _clear_search(self):
        self.search_box.clear(); self._search_mode=False; self.search_clear_btn.setVisible(False)
        self._refresh_main()

    # ── רענון ──────────────────────────────────────
    def _clear_cat_widgets(self):
        for w2 in self.cat_widgets: w2.setParent(None)
        self.cat_widgets.clear()
        for i in reversed(range(self.sw_layout.count())):
            item=self.sw_layout.itemAt(i)
            if item and item.spacerItem(): self.sw_layout.removeItem(item)

    def _refresh_main(self):
        self._clear_cat_widgets(); self._search_mode=False; self.search_clear_btn.setVisible(False)
        try: inst={s["name"].lower() for s in get_installed_software()}
        except: inst=set()
        cats=CONFIG.data.get("categories",[]); sws=CONFIG.data.get("software",[])
        cat_map={}
        for sw in sws: cat_map.setdefault(sw.get("category","כלל"),[]).append(sw)
        shown=set()
        for cat in cats:
            csw=cat_map.get(cat["name"],[])
            if csw:
                w2=CategoryWidget(cat,csw,inst); w2.install_single_sw.connect(self._install_single)
                self.cat_widgets.append(w2); self.sw_layout.addWidget(w2); shown.add(cat["name"])
        for cn,csw in cat_map.items():
            if cn not in shown:
                w2=CategoryWidget({"id":cn,"name":cn,"description":""},csw,inst)
                w2.install_single_sw.connect(self._install_single)
                self.cat_widgets.append(w2); self.sw_layout.addWidget(w2)
        if not cat_map:
            lbl=QLabel(TR("no_software")); lbl.setStyleSheet("color:#aaa;font-size:14px;padding:30px;")
            lbl.setAlignment(Qt.AlignCenter); self.sw_layout.addWidget(lbl); self.cat_widgets.append(lbl)
        self.sw_layout.addStretch()
        self.setWindowTitle(TR("app_name")); self.title_lbl.setText(TR("app_name"))

    # ── עזרים ──────────────────────────────────────
    def _expand_all(self,e):
        for cw in self.cat_widgets:
            if isinstance(cw,CategoryWidget): cw.content.setVisible(e); cw.cbtn.setText("▼" if e else "▶")

    def _expand_all_descriptions(self,expand):
        """הרחב/כווץ את פאנל התיאור עבור כל התוכנות המוצגות (קטגוריות + תוצאות חיפוש)"""
        for cw in self.cat_widgets:
            if isinstance(cw,(CategoryWidget,SearchResultWidget)): cw.set_descriptions_expanded(expand)

    def _sel_all(self,s):
        for cw in self.cat_widgets:
            if isinstance(cw,(CategoryWidget,SearchResultWidget)): 
                if isinstance(cw,CategoryWidget): cw.chk.setChecked(s)
                else:
                    for w2 in cw.sw_widgets: w2.cb.setChecked(s)

    def _open_settings(self):
        if CONFIG.data.get("settings_password"):
            dlg=PasswordDialog("סיסמת הגדרות",self)
            if dlg.exec_()!=QDialog.Accepted or not CONFIG.check_password("settings_password",dlg.get_password()):
                show_warning(self,"שגיאה","סיסמה שגויה."); return
        SettingsWindow(self).exec_(); self._refresh_main()

    def _open_scan(self): InstalledScanDialog(self).exec_()

    def _get_selected(self):
        s=[]
        for cw in self.cat_widgets:
            if isinstance(cw,(CategoryWidget,SearchResultWidget)): s.extend(cw.get_selected())
        return s

    def _install_single(self,sw): self._run_install([sw])
    def _start_install(self):
        sel=self._get_selected()
        if not sel: show_warning(self,"שגיאה","לא נבחרו תוכנות."); return
        self._run_install(sel)

    def _stop_install(self):
        """עצירת ההתקנה — עם אישור"""
        lang=CONFIG.data.get("language","he")
        if lang=="he":
            title="עצור התקנה"; msg="האם אתה בטוח שברצונך לעצור את ההתקנה?\nהתוכנה הנוכחית תסיים התקנתה ואז תעצר."
        else:
            title="Stop Installation"; msg="Are you sure you want to stop the installation?\nThe current software will finish and then stop."
        mb=QMessageBox(self); mb.setWindowTitle(title); mb.setText(msg)
        mb.setIcon(QMessageBox.Warning)
        mb.setStandardButtons(QMessageBox.Yes|QMessageBox.No)
        mb.setLayoutDirection(Qt.RightToLeft if lang=="he" else Qt.LeftToRight)
        _translate_buttons(mb,lang)
        if mb.exec_()==QMessageBox.Yes:
            if self.worker and self.worker.isRunning():
                self.worker.request_stop()
                self.stop_btn.setEnabled(False)
                self.slbl.setText("⏹ עוצר התקנה לאחר התוכנה הנוכחית...")

    def _update_sel_count(self):
        """עדכון מונה תוכנות נבחרות"""
        sel=self._get_selected()
        n=len(sel)
        if n==0:
            self.sel_count_lbl.setText("לא נבחרו תוכנות")
            self.sel_count_lbl.setStyleSheet("color:#7f8c8d;font-size:12px;")
            self.sel_preview_btn.setEnabled(False)
        elif n==1:
            self.sel_count_lbl.setText("✔ נבחרה תוכנה אחת")
            self.sel_count_lbl.setStyleSheet("color:#27ae60;font-size:12px;font-weight:bold;")
            self.sel_preview_btn.setEnabled(True)
        else:
            self.sel_count_lbl.setText(f"✔ נבחרו {n} תוכנות")
            self.sel_count_lbl.setStyleSheet("color:#27ae60;font-size:12px;font-weight:bold;")
            self.sel_preview_btn.setEnabled(True)

    def _show_selected_preview(self):
        """הצג חלונית עם רשימת התוכנות הנבחרות (סמל + שם)"""
        sel=self._get_selected()
        if not sel: return
        dlg=QDialog(self)
        dlg.setWindowTitle(f"תוכנות נבחרות להתקנה ({len(sel)})")
        dlg.setLayoutDirection(get_dir()); dlg.setMinimumWidth(360)
        dlg.setWindowFlags(dlg.windowFlags()&~Qt.WindowContextHelpButtonHint)
        lay=QVBoxLayout(dlg)
        hdr=QLabel(f"<b>✔ {len(sel)} תוכנות נבחרות להתקנה:</b>")
        hdr.setStyleSheet("font-size:13px;color:#2c3e50;padding:4px;"); lay.addWidget(hdr)
        scroll=QScrollArea(); scroll.setWidgetResizable(True); scroll.setMaximumHeight(380)
        scroll.setStyleSheet("border:1px solid #dde;border-radius:6px;background:white;")
        inner=QWidget(); inner_lay=QVBoxLayout(inner); inner_lay.setSpacing(2); inner_lay.setContentsMargins(4,4,4,4)
        for sw in sel:
            row=QWidget()
            row.setStyleSheet("background:white;border-radius:4px;")
            rl=QHBoxLayout(row); rl.setContentsMargins(4,3,4,3); rl.setSpacing(8)
            il=QLabel(); il.setFixedSize(28,28); il.setScaledContents(True)
            rip=resolve_icon(sw.get("icon",""))
            if rip: il.setPixmap(QPixmap(rip).scaled(28,28,Qt.KeepAspectRatio,Qt.SmoothTransformation))
            else: il.setStyleSheet("background:#ecf0f1;border-radius:4px;")
            nl=QLabel(sw.get("name","")); nl.setStyleSheet("font-size:12px;font-weight:bold;color:#2c3e50;")
            cat=sw.get("category",""); cl=QLabel(cat); cl.setStyleSheet("font-size:10px;color:#95a5a6;")
            rl.addWidget(il); rl.addWidget(nl); rl.addStretch(); rl.addWidget(cl)
            inner_lay.addWidget(row)
        inner_lay.addStretch(); scroll.setWidget(inner); lay.addWidget(scroll)
        close_btn=QPushButton("סגור"); close_btn.clicked.connect(dlg.accept)
        close_btn.setStyleSheet("background:#2c3e50;color:white;border-radius:5px;padding:6px 18px;")
        lay.addWidget(close_btn,alignment=Qt.AlignLeft)
        dlg.exec_()

    def _run_install(self,selected):
        if self.worker and self.worker.isRunning(): show_warning(self,"שגיאה","התקנה כבר מתבצעת."); return
        try: inst_low={s["name"].lower() for s in get_installed_software()}
        except: inst_low=set()
        already=[sw for sw in selected if sw["name"].lower() in inst_low]
        if already:
            dlg=AlreadyInstalledDialog(already,self)
            if dlg.exec_()==QDialog.Accepted:
                skip=dlg.get_skipped_ids(); selected=[sw for sw in selected if sw["id"] not in skip]
            else: return
        if not selected: return
        # שמור session לפני התחלה
        save_session(selected,[])
        self.ibtn.setEnabled(False); self.stop_btn.setVisible(True); self.stop_btn.setEnabled(True)
        self.prog.setVisible(True)
        self.prog.setRange(0,len(selected)); self.prog.setValue(0)
        self.prog.setFormat(f"מתקין %v מתוך {len(selected)}")
        for cw in self.cat_widgets:
            if isinstance(cw,(CategoryWidget,SearchResultWidget)): cw.set_install_enabled(False)
        self.worker=InstallWorker(selected,self.sr.isChecked())
        self.worker.progress.connect(lambda d,t:(self.prog.setValue(d),save_session(selected[d:],self.worker.report)))
        self.worker.status.connect(self.slbl.setText)
        self.worker.sw_status.connect(self._on_sw_status)
        self.worker.need_manual.connect(self._on_need_manual)
        self.worker.finished_all.connect(self._on_done)
        self.worker.start()

    def _on_sw_status(self,sid,st):
        for cw in self.cat_widgets:
            if isinstance(cw,(CategoryWidget,SearchResultWidget)): cw.set_sw_status(sid,st)

    def _on_need_manual(self,sw):
        r=show_question(self,"התקנה ידנית",
            f"לא ניתן להתקין '{sw['name']}' בשקט.\nהאם להתקין ידנית?",QMessageBox.Yes|QMessageBox.No)
        if self.worker: self.worker.set_manual_decision(sw["id"],"manual" if r==QMessageBox.Yes else "skip")

    def _on_done(self,report):
        self._last_report=report; self.ibtn.setEnabled(True)
        self.prog.setVisible(False); self.stop_btn.setVisible(False)
        self.slbl.setText("✅ ההתקנה הסתיימה!")
        for cw in self.cat_widgets:
            if isinstance(cw,(CategoryWidget,SearchResultWidget)): cw.set_install_enabled(True)
        if self.nc.isChecked():
            try: winsound.MessageBeep(winsound.MB_ICONASTERISK)
            except: pass
        ReportDialog(report,self).exec_(); self._refresh_main()

    def _show_last_report(self):
        if self._last_report: ReportDialog(self._last_report,self).exec_()
        else: show_info(self, 'דו"ח',"אין דו\"ח זמין.")

# ══════════════ Entry point ══════════════
def check_tool_password():
    if CONFIG.data.get("tool_password"):
        dlg=PasswordDialog("מתקין תוכנות בקליק — נדרשת סיסמה")
        if dlg.exec_()!=QDialog.Accepted or not CONFIG.check_password("tool_password",dlg.get_password()):
            QMessageBox.critical(None,"שגיאה","סיסמה שגויה. הכלי ייסגר."); sys.exit(1)


def main():
    try:
        import locale; locale.setlocale(locale.LC_ALL,"Hebrew_Israel.1255")
    except: pass

    app=QApplication(sys.argv)
    lang=CONFIG.data.get("language","he")
    app.setLayoutDirection(Qt.RightToLeft if lang=="he" else Qt.LeftToRight)
    app.setApplicationName(APP_NAME); app.setFont(QFont("Segoe UI",10)); app.setStyle("Fusion")

    pal=QPalette()
    pal.setColor(QPalette.Window,          QColor(240,242,245))
    pal.setColor(QPalette.WindowText,      QColor(30,39,46))
    pal.setColor(QPalette.Base,            QColor(255,255,255))
    pal.setColor(QPalette.AlternateBase,   QColor(245,247,250))
    pal.setColor(QPalette.Button,          QColor(44,62,80))
    pal.setColor(QPalette.ButtonText,      QColor(255,255,255))
    pal.setColor(QPalette.Highlight,       QColor(39,174,96))
    pal.setColor(QPalette.HighlightedText, QColor(255,255,255))
    pal.setColor(QPalette.Link,            QColor(41,128,185))
    pal.setColor(QPalette.ToolTipBase,     QColor(44,62,80))
    pal.setColor(QPalette.ToolTipText,     QColor(255,255,255))
    app.setPalette(pal)

    # ── Splash screen (מוצג לפני החלון הראשי, 2.5 שניות) ──
    try:
        splash=SplashWindow(); splash.show(); app.processEvents()
        import time; time.sleep(2.5); splash.close(); app.processEvents()
    except: pass

    check_tool_password()

    # ── טעינת אייקון PNG מוטמע ──────────────────────────
    app_icon=get_app_icon()
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)

    w=MainWindow()
    if not app_icon.isNull():
        w.setWindowIcon(app_icon)
    w.show()
    sys.exit(app.exec_())


if __name__=="__main__":
    main()

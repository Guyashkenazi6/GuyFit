# PulseFit: שדרוג חוויית אימון

שדרוג ממוקד לקוד הקיים ב־JavaScript, ללא React, ללא שרת וללא מנוי. מבוסס על commit `bb165fa1721a795e74ff4055edc7f93b4659582c`.

## מה השתנה

- תרגיל אחד בכל מסך: תמונת ביצוע מהמאגר הקיים, דגשים, סטים ואימון קודם.
- מעבר הקודם/הבא ומחוות Swipe באזור התוכן, לא מקצה המסך ולא על שדות קלט.
- טיימר מנוחה ממוזער כברירת מחדל, הרחבה, השהיה, המשך, תוספת 30 שניות ודילוג.
- טיימר לפי שעת סיום מוחלטת, נשמר בין טעינות. חזרה מנעילה מעדכנת את הזמן, לא מנחשת כמה פעימות JavaScript הוחמצו.
- בחירת חלופה עם תמונה, חיפוש וסינון שריר/ציוד, גם במהלך האימון.
- סטים שהושלמו לפני החלפה נשמרים תחת התרגיל המקורי. סטים שלא סומנו בתרגיל שהוחלף נזרקים. לתרגיל החדש מתחילים סטים חדשים.
- שינוי תוכנית קבועה דורש סימון מפורש. ברירת המחדל היא שינוי האימון הנוכחי בלבד.
- היסטוריה מפורטת לפי תרגיל וסט, משקל שיא מתועד, טבלת התקדמות וחלוקת סטים לשרירים ב־28 ימים.
- שמירת סיכומים היסטוריים קיימים. לא ממציאים פירוט סטים שאינו קיים.
- אימות קלט, שמירה בכל שינוי, מניעת דריסה של אימון פעיל ואישור סיום.
- ייצוא/ייבוא JSON עם אימות נתונים. כשל שמירה מוצג ולא מסיים אימון כאילו נשמר.
- עותק התאוששות מקומי לפני השדרוג (`pulsefit-before-v2`) ולפני ייבוא (`pulsefit-before-import`). אלה אינם תחליף לגיבוי מחוץ לדפדפן.
- תיקון שורת נתונים פגומה בתרגיל גלגל בטן, גם בתוכניות ישנות.
- איקוני PNG ל־iPhone, ביטול תלות בפונטים מרוחקים ותמיכה ב־Offline לאחר טעינה ראשונה מלאה.
- בדיקות דפדפן ו־CI. הכנת workflow לפריסה ידנית ל־GitHub Pages, לא פריסה אוטומטית בדחיפה.

## התקנה מקובץ העדכון

הקובץ המצורף `pulsefit-upgrade.txt` הוא Git Patch מלא, כולל קבצים חדשים ואיקונים. אין לשנות את תוכנו, ואין צורך לשנות סיומת.

```sh
git clone https://github.com/Guyashkenazi6/GuyFit.git GuyFit-v2
cd GuyFit-v2
git switch -c feat/workout-experience
```

העבר את קובץ העדכון שהורדת אל `GuyFit-v2`, פתח את התיקייה ב־Cursor והרץ בטרמינל שלה:

```sh
git apply --check pulsefit-upgrade.txt
git apply pulsefit-upgrade.txt
```

אם הבדיקה הראשונה נכשלת, עצור. אל תשתמש ב־`--reject` ואל תדרוס קוד שונה. העדכון מבוסס על ה־commit המצוין בראש המסמך. אין להוסיף את קובץ העדכון עצמו ל־Git.

## הרצה מקומית

אין צורך ב־Node או npm להרצת האפליקציה:

```sh
python3 -m http.server 5173 --directory PulseFit/dist
```

פתח `http://localhost:5173` בדפדפן במחשב. ב־Windows אפשר להשתמש ב־`py -3` במקום `python3`.
אין לפתוח את HTML בלחיצה כפולה: Service Worker דורש localhost או HTTPS.
הנתונים המקומיים בכתובת הבדיקה נפרדים מנתוני האתר החי. אין למחוק נתוני Safari ואין להסיר את ה־PWA לצורך העדכון.

## בדיקות אוטומטיות

אם `uv` מותקן:

```sh
uv venv
uv pip install -r requirements-test.txt
uv run python -m playwright install chromium
uv run python -m unittest discover -s tests -v
```

לבדיקת WebKit, כשכל ספריות המערכת מותקנות:

```sh
uv run python -m playwright install --with-deps webkit
BROWSER=webkit uv run python -m unittest discover -s tests -v
```

השורה האחרונה היא תחביר macOS/Linux; ב־PowerShell הגדר קודם `$env:BROWSER="webkit"`.
ב־CI הספריות מותקנות על ידי Playwright. בדיקת WebKit אינה תחליף לבדיקה באייפון פיזי.

## Git ו־Pull Request

אחרי בדיקה מקומית:

```sh
git status --short
git diff --stat
git add PulseFit/dist tests .github/workflows README.md VERIFICATION.md requirements-test.txt .gitignore
git commit -m "feat: improve workout flow and preserve exercise history"
git push -u origin feat/workout-experience
```

פתח Pull Request מהענף `feat/workout-experience` אל `main`, בדוק את ה־diff והמתן לבדיקות. אל תמזג אם בדיקה נכשלת.
לא בוצעו push, merge או פריסה כחלק מהכנת החבילה.

## פריסה אופציונלית ל־GitHub Pages

**אם האתר כבר מתארח במקום אחר, אין לשנות שירות או כתובת כחלק מהשדרוג.** נתוני LocalStorage משויכים למקור האתר ולפרופיל הדפדפן. כתובת חדשה עלולה להיראות ריקה. גם נתוני Safari ו־PWA באייפון עשויים להיות נפרדים. גבה בכל סביבת שימוש בנפרד.

לאחר מיזוג ובחירה מפורשת להשתמש ב־Pages:

1. בריפו: Settings → Pages → Source: GitHub Actions.
2. Actions → `Deploy Pages (manual)` → Run workflow → בחר `main`.
3. Workflow יריץ בדיקות בשני דפדפנים ורק אז יפרוס. אם נדרשת הרשאת Pages או אישור Environment, יש להשלים אותם ידנית ב־GitHub.
4. הפריסה משמרת נתיב `PulseFit/dist/`, והכתובת ללא custom domain תהיה:
   `https://guyashkenazi6.github.io/GuyFit/PulseFit/dist/`
5. אם המקור או הנתיב הקיימים שונים, עצור והתאם את הפריסה לפני השימוש בנתונים אמיתיים.

ה־Service Worker החדש ממתין לסגירת חלונות הגרסה הקודמת. סגור את כל טאבי האתר ואת ה־PWA ואז פתח מחדש עם רשת. ייתכן שתידרש סגירה ופתיחה נוספת אחרי שהעדכון הורד. אל תנקה אחסון כדי לכפות עדכון.

## מבחן קבלה באייפון

1. Safari → האתר ב־HTTPS → שיתוף → הוסף למסך הבית.
2. התחל אימון, הזן משקל וחזרות וסמן סט. למשקל גוף הזן `0` בשדה המשקל. זה אינו משקל הגוף שלך בחישוב נפח.
3. הרחב ומזער את הטיימר. הוא ממשיך. נסה השהיה, המשך ו־30+ שניות.
4. עבור לתרגיל אחר בזמן המנוחה. ודא שהתמונה משתנה והטיימר נשאר.
5. חזור, החלף תרגיל אחרי סט אחד וודא שהתוכנית לא משתנה בלי סימון מפורש.
6. נעל את האייפון לדקה ופתח. ודא שהספירה משקפת זמן אמיתי.
7. סגור ופתח מחדש. ודא שהאימון והסטים שוחזרו.
8. אחרי טעינה ראשונה מלאה, הפעל מצב טיסה ובדוק רישום סטים ותמונות.
9. סיים אימון, בדוק נפח והיסטוריה לפי התרגיל המקורי והחלופה.
10. במדדים, הורד גיבוי לקבצים. בדוק שחזור קודם בסביבת ניסוי, לא על הנתונים היחידים שלך.

## מגבלות מפורשות

- אין הבטחה לצליל, רטט או התראה בזמן נעילת אייפון. אין Background Push או שרת התראות. לא נוסף צליל סיום.
- עדיין LocalStorage. אין סנכרון בין מכשירים, משתמשים או גיבוי ענן. בשני טאבים אפשר ליצור התנגשויות: השתמש בחלון אימון אחד בלבד.
- הסטטיסטיקה החדשה משתמשת בסטים מפורטים רק מהשדרוג והלאה. היסטוריה ישנה נשארת כסיכומים.
- התקדמות בתרגיל מוצגת בטבלה, לא בגרף חדש. גרף הנפח השבועי הקיים נשאר.
- התמונות והמאגר נשמרו מהריפו הקיים. לא בוצע אימות רישוי או אישור מקצועי לכל איור. אין כאן מאגר חדש עם רישיון מסחרי.
- נשארה תוכנית הפיצול הישנה, ללא הוספת מאגר רגליים או יצירת תוכנית מקצועית חדשה. אין לראות במחולל ייעוץ רפואי או תוכנית מאוזנת מאושרת.
- סטים בפלאנק עדיין משתמשים בשדה החזרות של המודל הקיים. אין עדיין מדידת סטים לפי משך זמן.
- שמירת סיכום גדול ל־LocalStorage עשויה להגיע למכסת הדפדפן. במקרה כשל מוצגת אזהרה ויש לייצא גיבוי לפני סגירה.

## מבנה

```text
PulseFit/dist/
  app.js                 # הקוד הקיים המשודרג, מודל נתונים וממשק
  index.html             # מסכים ותיבות בחירה
  upgrade.css            # התאמות מסך תרגיל, טיימר וייבוא
  styles.css             # העיצוב הקיים
  exercise-atlas.css     # פריסת התמונות הקיימות
  sw.js                  # Offline ועדכון מדורג
  manifest.webmanifest
  icon-180.png           # iPhone
  icon-192.png
  icon-512.png
  assets/                # תמונות מקוריות ללא שינוי
tests/test_app.py         # 10 תרחישי קבלה
.github/workflows/
  ci.yml
  pages.yml              # פריסה ידנית בלבד
```

## Prompt מוכן ל־Cursor Composer

פתח Composer עם `Cmd + I` במק או `Ctrl + I` ב־Windows והדבק:

```text
This is my personal PulseFit repository. Read README.md and inspect the current diff.
Do not rewrite the app or change frameworks. Do not push, merge, deploy, or delete data.
Help me run the static app from PulseFit/dist, run tests/test_app.py, and understand
any failing check. Preserve pulsefit-state-v1, legacy summary history, completed
sets under their original exercise IDs, and the non-blocking deadline-based timer.
Before changing behavior, explain the proposed diff and wait for my approval.
```

# PulseFit

אפליקציית אימוני כוח אישית בעברית, RTL, ללא שרת או מנוי. הקוד המפורסם נמצא ב־`PulseFit/dist`.

## תרגילי רגליים

- 7 תרגילים: סקוואט במשקל גוף, גובלט סקוואט, מכרע לאחור, סקוואט בולגרי, דדליפט רומני בדאמבלים, גשר ישבן והרמת עקבים.
- איורי SVG מקוריים ומקומיים עם שני שלבי תנועה, ללא תלות בשירות תמונות חיצוני.
- שרירים עיקריים ומסייעים, שלבי ביצוע, נשימה, טעויות וגרסה קלה.
- קטגוריית רגליים בספרייה, בתיבת החלפת תרגיל ובמדדים; איורים והנחיות גם במהלך אימון.
- תוכנית חדשה כוללת יום רגליים רביעי עם 5 תרגילים, 3 סטים לתרגיל. זוהי ברירת מחדל ניתנת לשינוי, לא הוראה לבצע ארבעה אימונים בשבוע או תוכנית אישית רפואית.
- **תוכנית קיימת אינה משתנה אוטומטית.** הכפתור ״הוסף אימון רגליים לתוכנית הקיימת״ מוסיף יום בלי לשנות את שלושת הימים הקיימים. בזמן אימון פעיל התוספת חסומה.
- החזרות במכרעים ובסקוואט בולגרי הן לכל צד. בחר עומס וטווח תנועה המתאימים ליכולתך; הפסק בכאב חד. האיורים סכמטיים ואינם תחליף להדרכה מקצועית.

## פרטיות, שמירה ואופליין

מזהי תרגילים 1–48 ומפתח `pulsefit-state-v1` נשמרו. התרגילים החדשים משתמשים במזהים 49–55. פורמט הגיבוי הקיים (גרסה 2), היסטוריה ישנה, טיימר וסטים שבוצעו נשמרים.

ייצא גיבוי לפני עדכון. נתוני localhost לא עוברים אוטומטית ל־Pages. נתוני Safari ו־PWA עשויים להיות נפרדים; גבה בכל סביבת שימוש. לא מוחקים LocalStorage כדי לעדכן.

ה־Service Worker שומר גם את הקטלוג והאיורים החדשים לאופליין. גרסה חדשה ממתינה לסגירת כל הלשוניות הישנות; אין רענון כפוי במהלך אימון. לאחר פריסה, סיים אימון, סגור את כל לשוניות האתר ואת חלון ה־PWA ופתח מחדש בחיבור לרשת. אם עדיין מוצגת הגרסה הישנה, סגור ופתח שוב אחרי שההורדה הסתיימה.

## הרצה מקומית

```sh
python3 -m http.server 5173 --directory PulseFit/dist
```

פתח `http://localhost:5173`. לא פותחים HTML ישירות מקובץ.

## בדיקות

```sh
uv venv
uv pip install -r requirements-test.txt
uv run python -m playwright install --with-deps chromium webkit
node --check PulseFit/dist/legs.js
node --check PulseFit/dist/app.js
node --check PulseFit/dist/sw.js
uv run python -m unittest discover -s tests -v
BROWSER=webkit uv run python -m unittest discover -s tests -v
```

התקנת תלויות מערכת עשויה לדרוש הרשאות מנהל. ב־Windows אפשר להשתמש ב־`py -3` במקום `python3`; משתנה `BROWSER` מוגדר באמצעות `$env:BROWSER="webkit"` ב־PowerShell.

הבדיקות מכסות גם ייבוא/ייצוא, היסטוריה, מחיקה, שחזור אימון, כשל אחסון, תאימות לתוכנית ישנה, איורים, סינון, הוספת יום רגליים, נתיב Pages ואופליין. תוצאות הריצה בפועל ב־`VERIFICATION.md`.

## Git ו־CI/CD

1. פתח ענף פיתוח מה־`main` המעודכן והחל את העדכון.
2. בדוק מקומית, בצע commit ודחוף את ענף הפיתוח.
3. פתח Pull Request אל `main` והמתן ל־`Tests` בשני דפדפנים. אין פריסה מענף פיתוח.
4. לאחר מיזוג, `Deploy Pages` מופעל אוטומטית על ה־commit ב־`main`, מריץ שוב Chromium ו־WebKit ורק אם שניהם מצליחים מפרסם את אותו commit.
5. הפעלה ידנית נשארת זמינה דרך `Actions → Deploy Pages → Run workflow → main`.

`Settings → Pages → Source` צריך להיות `GitHub Actions`. הרשאות `pages: write` ו־`id-token: write` מוגבלות למשימת הפרסום. תור הפרסום אינו מבטל פרסום שכבר רץ. דרישות אישור של Environment, אם הוגדרו במאגר, עדיין חלות.

הכתובת נשמרת: `https://Guyashkenazi6.github.io/GuyFit/` מפנה ל־`/GuyFit/PulseFit/dist/`. אין שינוי מקור או נתיב אחסון.

## מבנה

```text
PulseFit/dist/
  app.js                  # התנהגות ומצב האפליקציה
  legs.js                 # קטלוג רגליים עם מזהים קבועים
  index.html
  exercise-atlas.css      # התאמת אטלסים ואיורי SVG עצמאיים
  sw.js                   # cache v6, עדכון מדורג ללא דריסת נתונים
  assets/legs/49.svg       # איורים מקוריים 49.svg עד 55.svg
  assets/                 # האטלסים הקיימים נשמרו
.github/workflows/
  ci.yml                  # בדיקות PR ו־main
  pages.yml               # בדיקות ואז פרסום main אוטומטי או ידני
tests/test_app.py
```

## בדיקה ידנית לפני שימוש אמיתי

- באייפון: בדוק ספריית רגליים, חלון ההנחיות, האיור, שדות משקל וחזרות והחלפת תרגיל.
- ייצא וייבא גיבוי בסביבת ניסוי; אל תסתמך על העותק היחיד של האימונים שלך.
- ודא שיום רגליים נוסף לתוכנית הישנה בלי החלפת שאר הימים.
- לאחר טעינה מלאה בדוק מצב טיסה ושחזור אימון.
- בדוק את ריצת GitHub Actions בפועל ואת האתר לאחר הפריסה.

### Machine leg exercises

The legs library includes leg extension (56) and seated leg curl (57) with local illustrations and Hebrew instructions. Use the exercise replacement picker to add either to an existing workout. Existing programs are not modified. Seated curl requires a machine explicitly supporting that mode; ask a gym instructor to confirm and adjust it.

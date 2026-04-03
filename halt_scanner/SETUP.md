# HaltScanner – הוראות התקנה

## מה המערכת עושה
1. **סורקת** הודעות בורסה (Maya/Bizportal) כל 5 דקות
2. **מזהה** הפסקות מסחר (45 דקות) אחרי הודעה מהותית
3. **שואלת Claude AI** – מי הספקים/שותפים הנסחרים של החברה?
4. **בודקת** אם הספקים לא זזו מספיק (פחות מ-60% ממניה הראשית)
5. **שולחת התראה** לטלגרם עם ניתוח קצר

---

## התקנה (5 דקות)

### שלב 1 – Python
ודא שיש Python 3.10+ מותקן:
```bash
python --version
```

### שלב 2 – חבילות
```bash
cd halt_scanner
pip install -r requirements.txt
```

### שלב 3 – Telegram Bot
1. פתח Telegram → חפש **@BotFather**
2. שלח `/newbot` → תן שם → תקבל **TOKEN**
3. שלח `/start` לבוט החדש שלך
4. פתח: `https://api.telegram.org/bot<TOKEN>/getUpdates`
5. העתק את `chat.id` מהתוצאה

### שלב 4 – Anthropic API Key
1. היכנס ל-https://console.anthropic.com
2. Settings → API Keys → Create Key
3. העתק את המפתח

### שלב 5 – config.yaml
ערוך את הקובץ `config.yaml`:
```yaml
telegram:
  bot_token: "1234567890:ABC..."   ← הכנס את ה-TOKEN
  chat_id: "123456789"             ← הכנס את ה-CHAT_ID

anthropic:
  api_key: "sk-ant-..."            ← הכנס את ה-API KEY
```

---

## הרצה

### בדיקת חיבורים
```bash
python main.py --test
```
→ יישלח הודעת בדיקה לטלגרם שלך

### סריקה אחת
```bash
python main.py --once
```

### דמו עם חברה ספציפית
```bash
python main.py --demo טבע
python main.py --demo "בנק לאומי"
```

### מצב רגיל (כל 5 דקות)
```bash
python main.py
```

### Windows – הפעלה אוטומטית עם Windows
צור Task Scheduler:
1. פתח Task Scheduler → Create Basic Task
2. Trigger: כל יום בשעת פתיחת הבורסה (09:50)
3. Action: `python C:\path\to\halt_scanner\main.py`
4. אפשרות: סמן "Run whether user is logged on or not"

---

## מבנה הקבצים
```
halt_scanner/
├── main.py           ← נקודת כניסה, מריץ את הכל
├── scanner.py        ← לוגיקה ראשית
├── analyzer.py       ← Claude AI – מחלץ ספקים
├── config.yaml       ← הגדרות (ערוך אותו!)
├── requirements.txt  ← חבילות Python
├── connectors/
│   ├── maya_rss.py       ← שליפת הודעות בורסה
│   ├── yahoo_finance.py  ← מחירי מניות
│   └── pdf_parser.py     ← ניתוח תשקיפים PDF
├── alerts/
│   ├── telegram_alert.py ← התראות Telegram
│   └── email_alert.py    ← התראות מייל (אופציונלי)
└── data/
    └── processed_halts.json  ← נוצר אוטומטית
```

---

## הגדרות חשובות ב-config.yaml

| פרמטר | ברירת מחדל | הסבר |
|-------|-----------|------|
| `scanning.interval_minutes` | 5 | כל כמה דקות לסרוק |
| `scanning.price_lag_threshold` | 0.6 | ספק שעלה פחות מ-60% → התראה |
| `scanning.max_suppliers_to_check` | 3 | כמה ספקים לבדוק (חוסך עלות API) |
| `alerts.min_price_change_pct` | 1.0 | מניה ראשית חייבת לעלות לפחות 1% |

---

## עלות משוערת
- Claude API: ~$0.01-0.05 לניתוח אחד
- בשוק רגיל: 1-3 הפסקות ביום = ~$0.10-0.15/יום
- ב-Yahoo Finance: חינם

---

## פתרון בעיות

**"לא ניתן לשלוף מחיר"** → ייתכן שהבורסה סגורה (שעות מסחר: 09:45-17:25)

**"שגיאת Telegram"** → בדוק שה-TOKEN וה-CHAT_ID נכונים

**"לא נמצאו הודעות"** → בדוק חיבור לאינטרנט; RSS של Bizportal עלול להיות מאט

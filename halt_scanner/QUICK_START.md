# HaltScanner Pro – מדריך התקנה מהיר

## מה זה עושה?
סוכן אוטונומי שמנטר הפסקות מסחר בבורסת ת"א ומזהה הזדמנויות:
1. סורק הודעות בורסה כל 5 דקות
2. מזהה הפסקות מסחר (45 דקות)
3. מנתח תשקיפים למציאת ספקים/שותפים נסחרים
4. בודק אם הספקים לא זזו (הזדמנות!)
5. שולח התראה לטלגרם + אימייל

## התקנה (5 דקות)

### שלב 1: התקנה אוטומטית
```bash
cd halt_scanner
python setup_scanner.py
```
עקוב אחרי ההוראות – ייצור API keys ויגדיר הכל.

### שלב 2 (אלטרנטיבה): הגדרה ידנית

#### Telegram Bot (2 דקות)
1. פתח Telegram → חפש `@BotFather`
2. שלח `/newbot` → בחר שם → העתק Token
3. שלח הודעה לבוט שיצרת
4. פתח: `https://api.telegram.org/bot<TOKEN>/getUpdates`
5. מצא: `"chat":{"id": XXXXXXX}` – זה ה-Chat ID

#### Anthropic API (1 דקה)
1. גש ל-[console.anthropic.com](https://console.anthropic.com)
2. Settings → API Keys → Create Key
3. העתק ל-config.yaml

#### Gmail (2 דקות, אופציונלי)
1. Google Account → Security → 2-Step Verification (הפעל)
2. Security → App Passwords → צור סיסמה חדשה
3. העתק ל-config.yaml

#### עדכן config.yaml
```yaml
telegram:
  bot_token: "1234567890:AAH..."
  chat_id: "987654321"
anthropic:
  api_key: "sk-ant-..."
email:
  enabled: true
  username: "you@gmail.com"
  password: "xxxx xxxx xxxx xxxx"
```

### שלב 3: בדיקה
```bash
python main.py --test
```

### שלב 4: הפעלה
```bash
# הפעלה רגילה (foreground)
python main.py

# סריקה אחת
python main.py --once

# הפעלה ברקע (daemon)
python service.py start

# דמו
python main.py --demo TEVA

# סיכום יומי
python main.py --summary
```

## הפעלה ברקע (Windows)

### אפשרות א: run_scanner.bat
לחיצה כפולה על `run_scanner.bat`

### אפשרות ב: service.py
```bash
python service.py start     # הפעלה
python service.py status    # מצב
python service.py stop      # עצירה
```

### אפשרות ג: Task Scheduler
1. פתח Task Scheduler
2. Create Basic Task → "HaltScanner"
3. Trigger: At startup
4. Action: Start a program
5. Program: `python`
6. Arguments: `C:\path\to\halt_scanner\main.py`
7. Start in: `C:\path\to\halt_scanner`

## Deploy לענן (Railway)

### הפעלה
```bash
# התקן Railway CLI
npm install -g @railway/cli

# Login
railway login

# Init + Deploy
cd halt_scanner
railway init
railway up
```

### הגדר Environment Variables ב-Railway
```
ANTHROPIC_API_KEY=sk-ant-...
TELEGRAM_BOT_TOKEN=123456:AAH...
TELEGRAM_CHAT_ID=987654321
```

## מבנה הקבצים
```
halt_scanner/
├── main.py              # נקודת כניסה
├── scanner.py           # לוגיקה ראשית
├── analyzer.py          # ניתוח AI (Claude)
├── config.yaml          # הגדרות
├── setup_scanner.py     # התקנה אוטומטית
├── run_scanner.bat      # הפעלה מהירה Windows
├── service.py           # daemon עם auto-restart
├── health_server.py     # health check לענן
├── Dockerfile           # deploy לענן
├── railway.toml         # Railway config
├── requirements.txt     # dependencies
├── connectors/
│   ├── maya_rss.py      # RSS בורסה
│   ├── yahoo_finance.py # מחירי מניות
│   └── pdf_parser.py    # תשקיפים
├── alerts/
│   ├── telegram_alert.py
│   └── email_alert.py
├── data/                # state + logs
└── logs/                # log files
```

## מנגנוני בטיחות
- **Rate limiting**: מקסימום 20 קריאות API בשעה
- **Budget**: תקרת $5/יום (ניתן לשנות)
- **Cooldown**: 2 דקות מינימום בין התראות
- **Confidence filter**: רק ספקים עם ביטחון medium+
- **שעות מסחר**: סריקה רק א-ה 09:45-17:30
- **Auto-restart**: service.py מתאושש מקריסות

## טיפים
- סיכום יומי נשלח ב-17:45 (ניתן לשנות ב-config)
- לוגים נשמרים ב-`logs/` לפי תאריך
- היסטוריית התראות ב-`data/daily_log.json`
- מעקב עלויות ב-`data/budget_tracker.json`

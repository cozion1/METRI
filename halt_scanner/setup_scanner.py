"""
setup_scanner.py – התקנה אוטומטית של HaltScanner Pro
מתקין dependencies, מגדיר API keys, ובודק חיבורים
הרץ: python setup_scanner.py
"""
import subprocess
import sys
import os
import yaml
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config.yaml"
REQ_PATH = Path(__file__).parent / "requirements.txt"

LOGO = """
╔══════════════════════════════════════╗
║     HaltScanner Pro – התקנה          ║
║     סורק הפסקות מסחר אוטונומי       ║
╚══════════════════════════════════════╝
"""


def check_python():
    """בדיקת גרסת Python."""
    v = sys.version_info
    print(f"\n1. Python: {v.major}.{v.minor}.{v.micro}", end=" ")
    if v.major >= 3 and v.minor >= 9:
        print("OK")
        return True
    else:
        print("צריך Python 3.9+!")
        return False


def install_dependencies():
    """התקנת חבילות Python."""
    print("\n2. מתקין dependencies...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", str(REQ_PATH), "-q"],
            stdout=subprocess.DEVNULL,
        )
        print("   OK – כל החבילות הותקנו")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   שגיאה: {e}")
        return False


def setup_telegram():
    """הגדרת Telegram Bot."""
    print("\n3. הגדרת Telegram Bot")
    print("   ---")
    print("   א. פתח Telegram וחפש @BotFather")
    print("   ב. שלח /newbot ועקוב אחרי ההוראות")
    print("   ג. העתק את ה-Bot Token שתקבל")
    print("   ---")

    token = input("   הדבק Bot Token (או Enter לדלג): ").strip()
    if not token:
        return None, None

    print("\n   עכשיו צריך את ה-Chat ID שלך:")
    print("   א. שלח הודעה כלשהי לבוט שיצרת")
    print(f"   ב. פתח: https://api.telegram.org/bot{token}/getUpdates")
    print('   ג. חפש "chat":{"id": XXXXXXX}')

    chat_id = input("   הדבק Chat ID: ").strip()
    return token, chat_id


def setup_anthropic():
    """הגדרת Anthropic API."""
    print("\n4. הגדרת Anthropic API")
    print("   ---")
    print("   א. גש ל-console.anthropic.com")
    print("   ב. Settings → API Keys → Create Key")
    print("   ---")

    api_key = input("   הדבק API Key (או Enter לדלג): ").strip()
    return api_key


def setup_email():
    """הגדרת Email."""
    print("\n5. הגדרת Email (אופציונלי)")
    answer = input("   רוצה לקבל התראות גם במייל? (y/n): ").strip().lower()

    if answer != "y":
        return None

    print("\n   להגדרת Gmail App Password:")
    print("   א. Google Account → Security → 2-Step Verification (חייב להיות מופעל)")
    print("   ב. Security → App Passwords → Create")
    print("   ג. בחר 'Mail' ו-'Other (Custom name)' → צור")

    email_addr = input("   כתובת Gmail שלך: ").strip()
    app_pass = input("   App Password (16 תווים): ").strip()
    extra = input("   מייל נוסף לשליחה (Enter לדלג): ").strip()

    return {
        "email": email_addr,
        "password": app_pass,
        "extra": extra,
    }


def update_config(telegram_token, telegram_chat, anthropic_key, email_data):
    """עדכון config.yaml עם ההגדרות."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if telegram_token:
        config["telegram"]["bot_token"] = telegram_token
    if telegram_chat:
        config["telegram"]["chat_id"] = telegram_chat
    if anthropic_key:
        config["anthropic"]["api_key"] = anthropic_key

    if email_data:
        config["email"]["enabled"] = True
        config["email"]["username"] = email_data["email"]
        config["email"]["password"] = email_data["password"]
        recipients = [email_data["email"]]
        if email_data.get("extra"):
            recipients.append(email_data["extra"])
        config["email"]["recipients"] = recipients
        config["alerts"]["enable_email"] = True

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print("\n   config.yaml עודכן בהצלחה!")


def run_test():
    """הרצת בדיקה."""
    print("\n6. מריץ בדיקת חיבורים...")
    subprocess.call([sys.executable, "main.py", "--test"])


def main():
    print(LOGO)

    if not check_python():
        return

    if not install_dependencies():
        return

    telegram_token, telegram_chat = setup_telegram()
    anthropic_key = setup_anthropic()
    email_data = setup_email()

    update_config(telegram_token, telegram_chat, anthropic_key, email_data)

    answer = input("\nרוצה להריץ בדיקת מערכת? (y/n): ").strip().lower()
    if answer == "y":
        run_test()

    print("\n" + "=" * 50)
    print("  ההתקנה הושלמה!")
    print("")
    print("  הפעלה:")
    print("    python main.py          – מצב רגיל (סריקה כל 5 דק')")
    print("    python main.py --once   – סריקה אחת")
    print("    python main.py --test   – בדיקת חיבורים")
    print("    python main.py --demo TEVA – דמו")
    print("")
    print("  או הרץ: run_scanner.bat   – הפעלה מהירה")
    print("=" * 50)


if __name__ == "__main__":
    main()

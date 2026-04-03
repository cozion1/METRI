"""
service.py – שירות רקע עם auto-restart
מריץ את HaltScanner כ-daemon שמתאושש אוטומטית מקריסות

הפעלה:
  python service.py start    – הפעלה ברקע
  python service.py stop     – עצירה
  python service.py status   – בדיקת מצב
  python service.py restart  – הפעלה מחדש
"""
import sys
import os
import time
import signal
import subprocess
import logging
from pathlib import Path
from datetime import datetime

SERVICE_DIR = Path(__file__).parent
PID_FILE = SERVICE_DIR / "data" / "scanner.pid"
LOG_DIR = SERVICE_DIR / "logs"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [Service] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("Service")


def get_pid() -> int:
    """מחזיר PID של התהליך הרץ, או 0."""
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            # בדוק אם התהליך חי
            if sys.platform == "win32":
                result = subprocess.run(
                    ["tasklist", "/fi", f"PID eq {pid}"],
                    capture_output=True, text=True
                )
                if str(pid) in result.stdout:
                    return pid
            else:
                os.kill(pid, 0)
                return pid
        except (ValueError, OSError, ProcessLookupError):
            pass
    return 0


def start():
    """מתחיל את השירות ברקע עם auto-restart."""
    existing = get_pid()
    if existing:
        print(f"HaltScanner כבר רץ (PID: {existing})")
        return

    LOG_DIR.mkdir(exist_ok=True)
    (SERVICE_DIR / "data").mkdir(exist_ok=True)

    print("מפעיל HaltScanner Pro ברקע...")

    if sys.platform == "win32":
        # Windows: pythonw for background
        proc = subprocess.Popen(
            [sys.executable, str(SERVICE_DIR / "service.py"), "_run"],
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
            stdout=open(LOG_DIR / "service.log", "a", encoding="utf-8"),
            stderr=subprocess.STDOUT,
        )
    else:
        proc = subprocess.Popen(
            [sys.executable, str(SERVICE_DIR / "service.py"), "_run"],
            stdout=open(LOG_DIR / "service.log", "a", encoding="utf-8"),
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )

    PID_FILE.write_text(str(proc.pid))
    print(f"HaltScanner Pro רץ ברקע (PID: {proc.pid})")
    print(f"לוג: {LOG_DIR / 'service.log'}")
    print("לעצירה: python service.py stop")


def stop():
    """עוצר את השירות."""
    pid = get_pid()
    if not pid:
        print("HaltScanner לא רץ")
        return

    print(f"עוצר HaltScanner (PID: {pid})...")
    try:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/pid", str(pid), "/f"],
                           capture_output=True)
        else:
            os.kill(pid, signal.SIGTERM)
    except Exception as e:
        print(f"שגיאה בעצירה: {e}")

    if PID_FILE.exists():
        PID_FILE.unlink()
    print("HaltScanner נעצר")


def status():
    """מציג מצב השירות."""
    pid = get_pid()
    if pid:
        print(f"HaltScanner Pro: רץ (PID: {pid})")

        # הצג שורה אחרונה מהלוג
        log_file = LOG_DIR / "service.log"
        if log_file.exists():
            lines = log_file.read_text(encoding="utf-8", errors="ignore").strip().split("\n")
            if lines:
                print(f"לוג אחרון: {lines[-1]}")
    else:
        print("HaltScanner Pro: לא רץ")


def _run():
    """הלולאה הפנימית עם auto-restart."""
    logger.info("Service started – auto-restart enabled")
    max_restarts = 10
    restart_count = 0
    main_py = str(SERVICE_DIR / "main.py")

    while restart_count < max_restarts:
        logger.info(f"מפעיל main.py (restart #{restart_count})")
        try:
            proc = subprocess.Popen(
                [sys.executable, main_py],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )

            # קרא output ושמור ללוג
            log_file = LOG_DIR / f"halt_scanner_{datetime.now().strftime('%Y%m%d')}.log"
            with open(log_file, "a", encoding="utf-8") as f:
                for line in iter(proc.stdout.readline, b""):
                    decoded = line.decode("utf-8", errors="replace")
                    f.write(decoded)
                    f.flush()

            exit_code = proc.wait()
            logger.warning(f"main.py נסגר עם קוד {exit_code}")

        except Exception as e:
            logger.error(f"שגיאה: {e}")

        restart_count += 1
        wait = min(30 * restart_count, 300)  # max 5 min between restarts
        logger.info(f"ממתין {wait} שניות לפני restart...")
        time.sleep(wait)

    logger.error(f"חריגה ממגבלת restarts ({max_restarts}). עוצר.")


def main():
    if len(sys.argv) < 2:
        print("שימוש: python service.py [start|stop|status|restart]")
        return

    cmd = sys.argv[1].lower()

    if cmd == "start":
        start()
    elif cmd == "stop":
        stop()
    elif cmd == "status":
        status()
    elif cmd == "restart":
        stop()
        time.sleep(2)
        start()
    elif cmd == "_run":
        _run()
    else:
        print(f"פקודה לא מוכרת: {cmd}")
        print("שימוש: python service.py [start|stop|status|restart]")


if __name__ == "__main__":
    main()

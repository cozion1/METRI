"""
email_alert.py – שליחת התראות במייל (Gmail / SMTP)
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
from datetime import datetime


def send_alert(
    smtp_server: str,
    smtp_port: int,
    username: str,
    password: str,
    recipients: List[str],
    halt_info: Dict,
    suppliers: List[Dict],
    analysis: Optional[str] = None,
) -> bool:
    subject = _build_subject(halt_info)
    html_body = _build_html_body(halt_info, suppliers, analysis)
    plain_body = _build_plain_body(halt_info, suppliers, analysis)
    recipients = [r for r in recipients if r]  # filter empty strings
    return _send_email(
        smtp_server, smtp_port, username, password,
        recipients, subject, html_body, plain_body
    )


def send_test(
    smtp_server: str,
    smtp_port: int,
    username: str,
    password: str,
    recipients: List[str],
) -> bool:
    """שולח מייל בדיקה."""
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    subject = "HaltScanner Pro – בדיקת מערכת"
    html = f"""
    <html dir='rtl'>
    <body style='font-family:Arial,sans-serif;direction:rtl'>
        <h2>HaltScanner Pro – בדיקת מערכת</h2>
        <p>המערכת פעילה ומחוברת!</p>
        <p>זמן: {now}</p>
        <p style='color:#999'>הודעה אוטומטית מ-HaltScanner Pro</p>
    </body>
    </html>
    """
    plain = f"HaltScanner Pro – בדיקת מערכת\nזמן: {now}\nהמערכת פעילה!"
    recipients = [r for r in recipients if r]
    return _send_email(smtp_server, smtp_port, username, password,
                       recipients, subject, html, plain)


def send_summary(
    smtp_server: str,
    smtp_port: int,
    username: str,
    password: str,
    recipients: List[str],
    summary_text: str,
) -> bool:
    """שולח סיכום יומי במייל."""
    today = datetime.now().strftime("%d/%m/%Y")
    subject = f"HaltScanner Pro – סיכום יומי {today}"
    # Convert markdown bold to HTML
    html_text = summary_text.replace("*", "<strong>").replace("\n", "<br>")
    html = f"""
    <html dir='rtl'>
    <body style='font-family:Arial,sans-serif;direction:rtl;max-width:600px;margin:0 auto'>
        <h2 style='color:#2c3e50'>HaltScanner Pro – סיכום יומי</h2>
        <div style='background:#f8f9fa;padding:16px;border-radius:8px'>
            {html_text}
        </div>
        <hr>
        <p style='color:#999;font-size:12px'>HaltScanner Pro – שמירה על שקט נפשי</p>
    </body>
    </html>
    """
    recipients = [r for r in recipients if r]
    return _send_email(smtp_server, smtp_port, username, password,
                       recipients, subject, html, summary_text)


def _build_subject(halt_info: Dict) -> str:
    company = halt_info.get("company", "לא ידוע")
    change = halt_info.get("change_pct")
    change_str = f" ({change:+.1f}%)" if change else ""
    return f"HaltScanner: הפסקת מסחר – {company}{change_str}"


def _build_html_body(
    halt_info: Dict,
    suppliers: List[Dict],
    analysis: Optional[str],
) -> str:
    company = halt_info.get("company", "לא ידוע")
    ticker = halt_info.get("ticker", "?")
    change = halt_info.get("change_pct")
    announcement = halt_info.get("announcement", "")
    link = halt_info.get("link", "")
    now = datetime.now().strftime("%d/%m/%Y %H:%M")

    change_html = f"<span style='color:green;font-weight:bold'>+{change:.1f}%</span>" if change and change > 0 else "N/A"

    rows = ""
    for s in suppliers:
        name = s.get("name", "?")
        sym = s.get("ticker") or "לא ידוע"
        s_change = s.get("change_pct")
        reason = s.get("reason", "")
        confidence = s.get("confidence", "")

        if s_change is not None:
            is_opp = change and s_change < change * 0.6
            color = "#e74c3c" if is_opp else "#27ae60"
            bg = "#fff3cd" if is_opp else "transparent"
            s_change_str = f"<span style='color:{color};font-weight:bold'>{s_change:+.1f}%</span>"
        else:
            s_change_str = "<em style='color:#999'>לא זמין</em>"
            bg = "transparent"

        conf_badge = {
            "high": "<span style='background:#27ae60;color:white;padding:2px 6px;border-radius:3px;font-size:11px'>גבוה</span>",
            "medium": "<span style='background:#f39c12;color:white;padding:2px 6px;border-radius:3px;font-size:11px'>בינוני</span>",
            "low": "<span style='background:#95a5a6;color:white;padding:2px 6px;border-radius:3px;font-size:11px'>נמוך</span>",
        }.get(confidence, "")

        rows += f"""
        <tr style='background:{bg}'>
            <td style='padding:8px;border-bottom:1px solid #eee'><strong>{name}</strong></td>
            <td style='padding:8px;border-bottom:1px solid #eee'>{sym}</td>
            <td style='padding:8px;border-bottom:1px solid #eee'>{s_change_str}</td>
            <td style='padding:8px;border-bottom:1px solid #eee'>{reason}</td>
            <td style='padding:8px;border-bottom:1px solid #eee'>{conf_badge}</td>
        </tr>"""

    analysis_html = f"""
    <div style='background:#eaf2f8;padding:14px;border-radius:6px;border-right:4px solid #3498db;margin:16px 0'>
        <strong>ניתוח AI:</strong><br>
        {analysis}
    </div>
    """ if analysis else ""

    link_html = f"<p><a href='{link}' style='color:#3498db'>לקריאת ההודעה המלאה</a></p>" if link else ""

    return f"""
    <html dir='rtl'>
    <body style='font-family:Arial,Helvetica,sans-serif;direction:rtl;max-width:650px;margin:0 auto;padding:20px'>
        <div style='background:linear-gradient(135deg,#e74c3c,#c0392b);color:white;padding:16px 20px;border-radius:8px;margin-bottom:16px'>
            <h2 style='margin:0'>הפסקת מסחר: {company} ({ticker})</h2>
            <p style='margin:8px 0 0;opacity:0.9'>זמן: {now} | מניה ראשית: {change_html}</p>
        </div>

        {'<p style="color:#555;font-size:14px;background:#f8f9fa;padding:12px;border-radius:4px">' + announcement[:300] + '</p>' if announcement else ''}

        <h3 style='color:#2c3e50;border-bottom:2px solid #eee;padding-bottom:8px'>ספקים/שותפים שנבדקו</h3>
        <table style='width:100%;border-collapse:collapse;font-size:14px'>
            <thead>
                <tr style='background:#34495e;color:white'>
                    <th style='padding:10px;text-align:right'>שם</th>
                    <th style='padding:10px;text-align:right'>סמל</th>
                    <th style='padding:10px;text-align:right'>שינוי</th>
                    <th style='padding:10px;text-align:right'>קשר</th>
                    <th style='padding:10px;text-align:right'>ביטחון</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>

        {analysis_html}
        {link_html}

        <hr style='margin-top:24px;border:none;border-top:1px solid #eee'>
        <p style='color:#999;font-size:11px;text-align:center'>
            HaltScanner Pro – שמירה על שקט נפשי<br>
            <em>אינו מהווה המלצת השקעה. יש לבצע בדיקה עצמאית.</em>
        </p>
    </body>
    </html>
    """


def _build_plain_body(
    halt_info: Dict,
    suppliers: List[Dict],
    analysis: Optional[str],
) -> str:
    company = halt_info.get("company", "?")
    change = halt_info.get("change_pct")
    lines = [
        f"הפסקת מסחר: {company}",
        f"שינוי: {change:+.1f}%" if change else "",
        "",
        "ספקים:",
    ]
    for s in suppliers:
        s_change = s.get("change_pct")
        s_change_str = f"{s_change:+.1f}%" if s_change is not None else "N/A"
        lines.append(f"  {s.get('name')} ({s.get('ticker','?')}): {s_change_str} - {s.get('reason','')}")

    if analysis:
        lines += ["", "ניתוח:", analysis]

    lines += ["", "--- אינו מהווה המלצת השקעה ---"]
    return "\n".join(lines)


def _send_email(
    smtp_server: str,
    smtp_port: int,
    username: str,
    password: str,
    recipients: List[str],
    subject: str,
    html_body: str,
    plain_body: str,
) -> bool:
    if not recipients:
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = username
        msg["To"] = ", ".join(recipients)

        msg.attach(MIMEText(plain_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.sendmail(username, recipients, msg.as_string())

        print(f"[Email] נשלח ל-{recipients}")
        return True

    except smtplib.SMTPException as e:
        print(f"[Email] שגיאת SMTP: {e}")
        return False
    except Exception as e:
        print(f"[Email] שגיאה: {e}")
        return False

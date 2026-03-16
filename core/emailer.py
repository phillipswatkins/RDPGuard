"""
RDP Guard - Email Alerter
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

log = logging.getLogger(__name__)


def send_permanent_block_alert(config, ip: str, attempt_count: int):
    if not config.EMAIL_ENABLED:
        return
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    subject = f"[RDP Guard] Permanent block issued for {ip}"
    body_html = f"""
<html><body style="font-family:Arial,sans-serif;color:#333;">
  <h2 style="color:#c0392b;">&#x1F6AB; RDP Guard — Permanent Block Issued</h2>
  <table style="border-collapse:collapse;width:100%;max-width:500px;">
    <tr><td style="padding:8px;background:#f5f5f5;"><b>IP Address</b></td><td style="padding:8px;">{ip}</td></tr>
    <tr><td style="padding:8px;background:#f5f5f5;"><b>Blocked At</b></td><td style="padding:8px;">{now}</td></tr>
    <tr><td style="padding:8px;background:#f5f5f5;"><b>Total Attempts</b></td><td style="padding:8px;">{attempt_count}</td></tr>
  </table>
  <p>This IP exceeded the permanent block threshold and has been added as a permanent Windows Firewall rule.</p>
  <hr style="border:none;border-top:1px solid #ddd;margin-top:24px;">
  <small style="color:#999;">Sent by RDP Guard</small>
</body></html>"""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.ALERT_FROM or config.SMTP_USER
    msg["To"] = config.ALERT_RECIPIENT
    msg.attach(MIMEText(body_html, "html"))
    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
        if config.SMTP_USE_TLS:
            server.starttls()
        server.login(config.SMTP_USER, config.SMTP_PASSWORD)
        server.sendmail(msg["From"], config.ALERT_RECIPIENT, msg.as_string())
    log.info(f"Alert sent to {config.ALERT_RECIPIENT} for {ip}")

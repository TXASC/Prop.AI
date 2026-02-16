# Notification helpers for nightly_preflight_backtest.py
import os
import logging
import pandas as pd
from config import (
    NOTIFY_EMAIL, SMTP_SERVER, SMTP_PORT, EMAIL_PASSWORD,
    NOTIFY_SLACK_WEBHOOK, USE_SLACK_NOTIFICATION, USE_EMAIL_NOTIFICATION, OUTPUT_DIR, LOGS_DIR
)

def send_email_notification(subject, body, attachment_path=None, logger=None):
    try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.base import MIMEBase
        from email import encoders
        sender = NOTIFY_EMAIL
        recipients = [NOTIFY_EMAIL] if isinstance(NOTIFY_EMAIL, str) else NOTIFY_EMAIL
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = ', '.join(recipients)
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(attachment_path)}')
                msg.attach(part)
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(sender, EMAIL_PASSWORD)
        server.sendmail(sender, recipients, msg.as_string())
        server.quit()
        if logger:
            logger.info(f"Email sent to {recipients}")
        return True
    except Exception as e:
        if logger:
            logger.error(f"Email notification failed: {e}")
        return False

def send_slack_notification(message, logger=None):
    try:
        import requests
        webhook_url = NOTIFY_SLACK_WEBHOOK
        if not webhook_url:
            if logger:
                logger.error("Slack webhook URL not configured.")
            return False
        payload = {"text": message}
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 200:
            if logger:
                logger.info("Slack notification sent.")
            return True
        else:
            if logger:
                logger.error(f"Slack notification failed: {response.text}")
            return False
    except Exception as e:
        if logger:
            logger.error(f"Slack notification error: {e}")
        return False

def build_notification_summary(eval_report_path):
    try:
        df = pd.read_csv(eval_report_path)
        summary = []
        for _, row in df.iterrows():
            summary.append(f"{row['check']}: {row['status']} | {row['suggestion']}")
        return '\n'.join(summary)
    except Exception as e:
        return f"Could not read evaluation report: {e}"

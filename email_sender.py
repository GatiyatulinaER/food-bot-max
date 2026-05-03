# email_sender.py
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailSender:
    def __init__(self, email_from: str, password: str, smtp_server: str, smtp_port: int = 465):
        self.email_from = email_from
        self.password = password
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.login = email_from

    def send_report(self, to_emails: list, report_path: str, period: str, building: str) -> bool:
        if not os.path.exists(report_path):
            logger.error(f"Файл не найден: {report_path}")
            return False

        period_names = {"daily": "Ежедневный", "weekly": "Еженедельный", "monthly": "Ежемесячный"}
        period_name = period_names.get(period, period)
        
        msg = MIMEMultipart()
        msg['From'] = self.email_from
        msg['To'] = ', '.join(to_emails)
        msg['Subject'] = f"[Бот-Ланчбокс] {period_name} отчёт - {building} - {datetime.now().strftime('%d.%m.%Y')}"

        body = f"""
        <html>
        <head><meta charset="UTF-8"></head>
        <body>
            <h2>📊 {period_name} отчёт по питанию</h2>
            <p><strong>🏫 Здание:</strong> {building}</p>
            <p><strong>📅 Дата:</strong> {datetime.now().strftime('%d.%m.%Y')}</p>
            <p>Отчёт во вложении.</p>
            <hr>
            <p>Сформировано автоматически ботом "Ланчбокс"</p>
        </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html', 'utf-8'))

        with open(report_path, 'rb') as attachment:
            part = MIMEBase('application', 'vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(report_path)}"')
            msg.attach(part)

        try:
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.login, self.password)
                server.send_message(msg)
            logger.info(f"✅ Отчёт для {building} отправлен на {', '.join(to_emails)}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка отправки: {e}")
            return False


# ========== НАСТРОЙКА ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ==========
# Собираем список email для Марченко из нескольких переменных
marchenko_emails = []

email1 = os.environ.get("EMAIL_TO_MARCHENKO_1", "")
if email1:
    marchenko_emails.append(email1)

email2 = os.environ.get("EMAIL_TO_MARCHENKO_2", "")
if email2:
    marchenko_emails.append(email2)

# Если нет отдельных переменных, пробуем старую
if not marchenko_emails:
    old_email = os.environ.get("EMAIL_TO_MARCHENKO", "")
    if old_email:
        marchenko_emails.append(old_email)

EMAIL_CONFIG = {
    "enabled": True,
    "service": "gmail",
    "from_email": os.environ.get("EMAIL_FROM", ""),
    "app_password": os.environ.get("EMAIL_PASSWORD", ""),
    "recipients": {
        "Марченко": marchenko_emails,
        "Танкистов": [
            os.environ.get("EMAIL_TO_TANKISTOV", ""),
        ]
    }
}

SMTP_CONFIG = {
    "gmail": {"server": "smtp.gmail.com", "port": 465},
}


def get_email_sender():
    if not EMAIL_CONFIG.get("enabled", False):
        return None
    if not EMAIL_CONFIG["from_email"] or not EMAIL_CONFIG["app_password"]:
        print("⚠️ Email не настроен: отсутствуют EMAIL_FROM или EMAIL_PASSWORD")
        return None
    return EmailSender(
        email_from=EMAIL_CONFIG["from_email"],
        password=EMAIL_CONFIG["app_password"],
        smtp_server="smtp.gmail.com",
        smtp_port=465
    )


def send_report_via_email(report_path: str, period: str, building: str) -> bool:
    sender = get_email_sender()
    if not sender:
        print("📧 Email отправка отключена или не настроена")
        return False
    
    recipients = EMAIL_CONFIG.get("recipients", {}).get(building, [])
    recipients = [r for r in recipients if r]  # Убираем пустые
    if not recipients:
        print(f"❌ Не указаны email получатели для здания {building}")
        return False
    
    return sender.send_report(recipients, report_path, period, building)


print("✅ email_sender.py загружен")
print(f"📧 Получатели Марченко: {EMAIL_CONFIG['recipients']['Марченко']}")
print(f"📧 Получатели Танкистов: {EMAIL_CONFIG['recipients']['Танкистов']}")

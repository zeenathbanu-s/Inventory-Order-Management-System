import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("EMAIL_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("EMAIL_PORT", 587))
        self.username = os.getenv("EMAIL_USERNAME")
        self.password = os.getenv("EMAIL_PASSWORD")

    async def send_email(self, to_email: str, subject: str, body: str):
        try:
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = to_email
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'html'))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            text = msg.as_string()
            server.sendmail(self.username, to_email, text)
            server.quit()
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    async def send_low_stock_alert(self, product_name: str, current_stock: int, admin_email: str):
        subject = f"Low Stock Alert: {product_name}"
        body = f"""
        <html>
        <body>
            <h2>Low Stock Alert</h2>
            <p><strong>Product:</strong> {product_name}</p>
            <p><strong>Current Stock:</strong> {current_stock}</p>
            <p>Please restock this item soon.</p>
        </body>
        </html>
        """
        return await self.send_email(admin_email, subject, body)

    async def send_order_confirmation(self, order_number: str, customer_email: str, total_amount: float):
        subject = f"Order Confirmation - {order_number}"
        body = f"""
        <html>
        <body>
            <h2>Order Confirmation</h2>
            <p>Thank you for your order!</p>
            <p><strong>Order Number:</strong> {order_number}</p>
            <p><strong>Total Amount:</strong> ${total_amount:.2f}</p>
            <p>We'll notify you when your order ships.</p>
        </body>
        </html>
        """
        return await self.send_email(customer_email, subject, body)

email_service = EmailService()
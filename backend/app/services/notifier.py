import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from backend.app.config import settings

logger = logging.getLogger("price_tracker.alerts")


def send_price_drop_alert(
    user_email: str,
    product_title: str,
    product_url: str,
    target_price: float,
    current_price: float,
    currency: str = "INR"
) -> Dict[str, Any]:
    """
    Handles alert dispatching when a price drops to or below target price.
    Always logs the alert, and sends an email if SMTP is enabled.
    """
    savings = target_price - current_price
    savings_pct = (savings / target_price) * 100 if target_price > 0 else 0.0

    message_text = (
        f"🚨 PRICE DROP ALERT! 🚨\n"
        f"Product: {product_title}\n"
        f"Current Price: {currency} {current_price:.2f}\n"
        f"Target Price: {currency} {target_price:.2f}\n"
        f"You save: {currency} {savings:.2f} ({savings_pct:.1f}% below target!)\n"
        f"Link: {product_url}\n"
    )

    logger.warning(
        f"[ALERT DISPATCHED] User: {user_email} | Product: '{product_title}' | "
        f"Current: {current_price} <= Target: {target_price} (Saved: {savings:.2f})"
    )

    email_sent = False
    if settings.SMTP_ENABLED and settings.SMTP_USER and settings.SMTP_PASSWORD:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"Price Alert: '{product_title}' dropped to {currency} {current_price:.2f}!"
            msg["From"] = settings.ALERT_FROM_EMAIL
            msg["To"] = user_email

            html_body = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
                <h2 style="color: #16a34a;">🎉 Price Drop Alert!</h2>
                <p>Good news! A product you are tracking has dropped to or below your target price.</p>
                <div style="background-color: #f8fafc; padding: 16px; border-radius: 6px; margin: 16px 0;">
                    <h3 style="margin-top: 0;">{product_title}</h3>
                    <p style="font-size: 1.25rem; font-weight: bold; color: #16a34a; margin: 8px 0;">
                        Current Price: {currency} {current_price:.2f}
                    </p>
                    <p style="color: #64748b; margin: 4px 0;">Your Target: {currency} {target_price:.2f}</p>
                    <p style="color: #0284c7; margin: 4px 0;">Discount: {currency} {savings:.2f} ({savings_pct:.1f}%)</p>
                </div>
                <a href="{product_url}" style="display: inline-block; background-color: #2563eb; color: white; padding: 10px 20px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                    View Product Deal
                </a>
            </div>
            """
            msg.attach(MIMEText(message_text, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.ALERT_FROM_EMAIL, user_email, msg.as_string())
            email_sent = True
            logger.info(f"Email alert successfully sent to {user_email}")
        except Exception as e:
            logger.error(f"Failed to send email alert to {user_email}: {e}")

    return {
        "alert_triggered": True,
        "email_sent": email_sent,
        "message": message_text,
        "savings": savings,
        "savings_pct": savings_pct
    }

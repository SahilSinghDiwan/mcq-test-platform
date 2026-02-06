import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging

from .config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class EmailService:
    @staticmethod
    async def send_email(
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        try:
            message = MIMEMultipart("alternative")
            message["From"] = settings.SMTP_FROM
            message["To"] = to_email
            message["Subject"] = subject
            
            if text_content:
                part1 = MIMEText(text_content, "plain")
                message.attach(part1)
            
            part2 = MIMEText(html_content, "html")
            message.attach(part2)
            
            async with aiosmtplib.SMTP(
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                use_tls=settings.SMTP_TLS
            ) as smtp:
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    await smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                await smtp.send_message(message)
            
            logger.info(f"Email sent to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    @staticmethod
    async def send_otp_email(email: str, otp: str) -> bool:
        subject = "Your MCQ Test Verification Code"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; }}
                .container {{ max-width: 600px; margin: 40px auto; background: white; 
                            border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 40px 30px; }}
                .otp-box {{ background: #f8f9fa; border: 2px dashed #667eea; 
                          border-radius: 8px; padding: 20px; text-align: center; margin: 30px 0; }}
                .otp-code {{ font-size: 36px; font-weight: bold; color: #667eea; 
                           letter-spacing: 8px; font-family: monospace; }}
                .warning {{ background: #fff3cd; border-left: 4px solid #ffc107; 
                          padding: 15px; margin: 20px 0; border-radius: 4px; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; 
                        color: #6c757d; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0;">MCQ Testing Platform</h1>
                    <p style="margin: 10px 0 0 0;">Verification Code</p>
                </div>
                <div class="content">
                    <p>Hello,</p>
                    <p>Please use the following code to verify your email:</p>
                    <div class="otp-box">
                        <div class="otp-code">{otp}</div>
                    </div>
                    <p style="text-align: center; color: #6c757d;">
                        Code expires in <strong>{settings.OTP_EXPIRY_MINUTES} minutes</strong>
                    </p>
                    <div class="warning">
                        <strong>Important:</strong>
                        <ul style="margin: 10px 0; padding-left: 20px;">
                            <li>Single attempt only</li>
                            <li>Tab switching will trigger warnings</li>
                            <li>Auto-submit after 2 warnings</li>
                            <li>Do not share this code</li>
                        </ul>
                    </div>
                    <p>If you didn't request this, ignore this email.</p>
                </div>
                <div class="footer">
                    <p>© 2026 MCQ Testing Platform. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        MCQ Testing Platform - Verification Code
        
        Your OTP: {otp}
        Expires in: {settings.OTP_EXPIRY_MINUTES} minutes
        
        If you didn't request this, ignore this email.
        """
        
        return await EmailService.send_email(
            to_email=email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
    
    @staticmethod
    async def send_test_completion_email(email: str, score: int, total: int) -> bool:
        percentage = (score / total * 100) if total > 0 else 0
        subject = "Test Completed - MCQ Testing Platform"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; background: #f4f4f4; }}
                .container {{ max-width: 600px; margin: 40px auto; background: white; 
                            padding: 30px; border-radius: 8px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white; padding: 20px; text-align: center; border-radius: 8px; }}
                .score {{ font-size: 48px; font-weight: bold; color: #667eea; 
                        text-align: center; margin: 30px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header"><h1>Test Completed!</h1></div>
                <p>Thank you for completing the test.</p>
                <div class="score">{score} / {total}</div>
                <p style="text-align: center;">Accuracy: <strong>{percentage:.1f}%</strong></p>
                <p>Our team will review your submission shortly.</p>
            </div>
        </body>
        </html>
        """
        
        return await EmailService.send_email(
            to_email=email,
            subject=subject,
            html_content=html_content
        )


email_service = EmailService()
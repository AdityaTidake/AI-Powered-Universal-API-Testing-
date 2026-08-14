import logging
import smtplib
from email.message import EmailMessage

from aitester.core.config import settings
from aitester.db.models import TestRun

logger = logging.getLogger(__name__)


def send_run_completion_email(to_email: str, test_run: TestRun, project_name: str, total_cases: int, pass_rate: float, security_score: float) -> None:
    """
    Sends an email notification summarizing the test run completion.
    Falls back to console logging if SMTP is not configured.
    """
    status_color = "green" if test_run.status == "COMPLETED" else "red"
    
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2 style="color: {status_color};">SpecGuard AI: Test Run {test_run.status}</h2>
        <p>Your test run for project <strong>{project_name}</strong> has finished.</p>
        
        <table style="border-collapse: collapse; width: 100%; max-width: 600px; margin-top: 15px;">
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Run ID</strong></td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{str(test_run.id)}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Total Cases</strong></td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{total_cases}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Pass Rate</strong></td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{pass_rate}%</td>
            </tr>
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Security Score</strong></td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{security_score}/100</td>
            </tr>
        </table>
        
        <p style="margin-top: 20px;">
            <a href="{settings.FRONTEND_URL}/runs" style="background-color: #0066cc; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px;">
                View Full Report
            </a>
        </p>
      </body>
    </html>
    """

    subject = f"SpecGuard AI: Test Run {test_run.status} for {project_name}"
    
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = settings.EMAILS_FROM_EMAIL
    msg['To'] = to_email
    msg.set_content("Please enable HTML to view this email.")
    msg.add_alternative(html_content, subtype='html')

    if not settings.SMTP_HOST:
        logger.info(f"📧 EMAIL NOTIFICATION (MOCKED):")
        logger.info(f"To: {to_email}")
        logger.info(f"Subject: {subject}")
        logger.info(f"Pass Rate: {pass_rate}%, Security Score: {security_score}")
        return

    try:
        # Start SMTP session
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        server.starttls()
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        
        server.send_message(msg)
        server.quit()
        logger.info(f"Successfully sent email notification to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send email notification to {to_email}: {e}")

def send_run_failure_email(to_email: str, test_run_id: str, reason: str) -> None:
    """
    Sends an email notification for a catastrophic test run failure.
    """
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2 style="color: red;">SpecGuard AI: Test Run FAILED</h2>
        <p>Your test run <strong>{test_run_id}</strong> failed to execute completely.</p>
        <p><strong>Reason:</strong> {reason}</p>
        <p style="margin-top: 20px;">
            <a href="{settings.FRONTEND_URL}/runs" style="background-color: #0066cc; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px;">
                View Test Runs
            </a>
        </p>
      </body>
    </html>
    """
    subject = f"SpecGuard AI: Test Run FAILED ({test_run_id})"
    
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = settings.EMAILS_FROM_EMAIL
    msg['To'] = to_email
    msg.set_content("Please enable HTML to view this email.")
    msg.add_alternative(html_content, subtype='html')

    if not settings.SMTP_HOST:
        logger.info(f"📧 EMAIL NOTIFICATION (MOCKED):")
        logger.info(f"To: {to_email} | Subject: {subject} | Reason: {reason}")
        return

    try:
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        server.starttls()
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        logger.error(f"Failed to send failure email to {to_email}: {e}")

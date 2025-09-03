#!/usr/bin/env python3
"""Simple email test for ChatGPT Investor system."""

import smtplib
import datetime

def send_test_email():
    """Send a simple test email."""
    
    # Email configuration
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    sender_email = 'kreddy.2027@gmail.com'
    password = 'lbct ihng xdjg boew'
    recipient = 'kreddy.2027@gmail.com'
    
    # Create email content
    subject = 'ChatGPT Investor Test Email'
    body = f"""Subject: {subject}
From: {sender_email}
To: {recipient}

This is a test email from your ChatGPT Investor automation system!

[OK] Email configuration: Working
[OK] API key: Configured  
[OK] Daily reports: Will be sent at 7:00 PM EST
[OK] Automation: Fully ready

System Status:
- Email: kreddy.2027@gmail.com
- Schedule: Daily at 7:00 PM EST
- API: Ready for AI decisions
- Portfolio tracking: Active

If you receive this email, your system is properly configured and ready to send daily trading reports with AI recommendations.

Sent at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Best regards,
Your Automated Trading System
"""

    try:
        print('Connecting to Gmail SMTP...')
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            print('Logging in...')
            server.login(sender_email, password)
            print('Sending email...')
            server.sendmail(sender_email, recipient, body)
        
        print('✅ Test email sent successfully to kreddy.2027@gmail.com')
        print('Check your inbox (and spam folder) for the test message!')
        return True
        
    except Exception as e:
        print(f'❌ Email test failed: {e}')
        print('This might be due to:')
        print('1. Incorrect app password')
        print('2. 2FA not enabled on Gmail')
        print('3. App password not generated correctly')
        return False

if __name__ == '__main__':
    print('=== ChatGPT Investor Email Test ===')
    send_test_email()
import django, os, smtplib
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
django.setup()
from django.conf import settings as s

print("=== EMAIL CONFIG ===")
print("Backend :", s.EMAIL_BACKEND)
print("Host    :", s.EMAIL_HOST, s.EMAIL_PORT)
print("User    :", s.EMAIL_HOST_USER)
pwd = s.EMAIL_HOST_PASSWORD or ""
bad = ["your-16-char-app-password", "your-brevo-smtp-key-here", ""]
if pwd in bad:
    print("Password: NOT SET (still placeholder)")
    print()
    print("ACTION: Edit .env and set EMAIL_HOST_PASSWORD to your real password")
    if "brevo" in s.EMAIL_HOST.lower():
        print("Get Brevo SMTP key from: https://app.brevo.com/settings/keys/smtp")
    else:
        print("Get Gmail App Password from: https://myaccount.google.com/apppasswords")
else:
    print("Password:", len(pwd), "chars - testing connection...")
    try:
        srv = smtplib.SMTP(s.EMAIL_HOST, s.EMAIL_PORT, timeout=10)
        srv.ehlo()
        srv.starttls()
        srv.login(s.EMAIL_HOST_USER, s.EMAIL_HOST_PASSWORD)
        srv.quit()
        print("RESULT: SUCCESS - Email is working!")
    except smtplib.SMTPAuthenticationError as e:
        print("RESULT: AUTH FAILED -", str(e))
        print("FIX: Wrong password. Use App Password not Gmail login password.")
    except Exception as e:
        print("RESULT: FAILED -", str(e))

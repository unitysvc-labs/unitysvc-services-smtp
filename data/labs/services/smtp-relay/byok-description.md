## SMTP Relay — Bring Your Own Key

Send emails through the UnitySVC SMTP gateway using your own SMTP server credentials (Gmail, SendGrid, Mailgun, Amazon SES, etc.).

### Setup

1. **Enroll** in this service on the UnitySVC platform
2. **Provide your SMTP credentials** as customer secrets during enrollment:
   - `SMTP_HOST` — your SMTP server hostname (e.g., `smtp.gmail.com`, `smtp.sendgrid.net`)
   - `SMTP_PORT` — SMTP port (typically `587` for STARTTLS, `465` for SSL)
   - `SMTP_USERNAME` — your SMTP username or email
   - `SMTP_PASSWORD` — your SMTP password or app-specific password

3. **Send email** through the UnitySVC SMTP gateway using your svcpass API key

### Usage

Configure your SMTP client with:
- **Server**: smtp.unitysvc.com (or localhost:2587 for local dev)
- **Port**: 587
- **Auth**: PLAIN or LOGIN
- **Username**: anything (ignored)
- **Password**: your svcpass API key

The gateway authenticates you, resolves your SMTP credentials from your enrollment, and relays the email to your configured SMTP server.

### Supported SMTP Providers

Any standard SMTP server works. Common providers:
- **Gmail**: smtp.gmail.com:587 (requires app password)
- **SendGrid**: smtp.sendgrid.net:587
- **Mailgun**: smtp.mailgun.org:587
- **Amazon SES**: email-smtp.us-east-1.amazonaws.com:587
- **Postmark**: smtp.postmarkapp.com:587
- **Custom**: any SMTP server with PLAIN/LOGIN auth

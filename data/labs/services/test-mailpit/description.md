## Test SMTP Relay

This is a test SMTP relay service. Emails sent through this service are captured by Mailpit and can be viewed at [mailpit.svcmarket.com](https://mailpit.svcmarket.com).

**No actual email delivery occurs** — this service is for testing the SMTP gateway only.

### Usage

Configure your SMTP client with:

- **Server**: smtp.unitysvc.com (or localhost:2587 for local dev)
- **Port**: 587
- **Auth**: PLAIN or LOGIN
- **Username**: anything (ignored)
- **Password**: your svcpass API key

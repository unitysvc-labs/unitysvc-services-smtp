# SMTP Relay (Multi-Enrollment) — `labs/smtp-relay-plus`

Send emails through the UnitySVC SMTP gateway using your own SMTP servers. Unlike the free `smtp-relay` (BYOK) service, this variant supports **multiple enrollments** — each one connects to a different SMTP server. Pricing: **$1 per 1,000 emails**.

## When to pick this over the free `smtp-relay`

- **Personal + Work** — one enrollment for Gmail, another for your company's SMTP.
- **Transactional + Marketing** — separate enrollments for SES (transactional) and Mailgun (marketing).
- **Multi-tenant** — different SMTP servers for different clients or projects.

If you only need **one** upstream SMTP, use the free [`smtp-relay`](../smtp-relay/) — this `-plus` exists for the multi-account case.

## What goes where: parameters vs. customer secrets

The non-secret pieces (host, port, username) are **enrollment parameters** stored on the enrollment row at enroll time. The **password** is a customer secret named by the parameter `password_secret`. This way:

- You can see all your enrollments' upstream config at a glance (no need to inspect secrets to find out which enrollment talks to which host).
- Rotating a password is one `usvc_seller secrets set` call — no re-enroll.
- Only sensitive material lives in the secrets store; nothing else.

| Parameter | Required | Default | What it is |
|---|---|---|---|
| `host` | optional | `mailpit.svcmarket.com` | SMTP hostname (a literal value). Default lands you on the platform's mailpit test sink. |
| `port` | optional | `1025` | SMTP port (literal). `1025` mailpit, `587` STARTTLS, `465` TLS. |
| `username` | optional | `""` | SMTP username (literal). Empty for mailpit. |
| `password_secret` | optional | `""` | **Name** of the customer secret holding the password. Resolved at request time. Leave empty for mailpit. |

## Setup

1. **Save the password for each upstream SMTP as a customer secret.** Use a name that makes the enrollment obvious — e.g.:

   ```bash
   usvc_seller secrets set GMAIL_SMTP_PASSWORD    --value "<gmail-app-password>"
   usvc_seller secrets set SENDGRID_SMTP_PASSWORD --value "<sendgrid-api-key>"
   ```

2. **Enroll once per upstream**, supplying `host`/`port`/`username` inline and `password_secret` as the name from step 1:

   ```json
   // Gmail
   { "host": "smtp.gmail.com",    "port": 587, "username": "you@gmail.com", "password_secret": "GMAIL_SMTP_PASSWORD" }
   ```
   ```json
   // SendGrid
   { "host": "smtp.sendgrid.net", "port": 587, "username": "apikey",        "password_secret": "SENDGRID_SMTP_PASSWORD" }
   ```

3. **Send mail** through each enrollment's gateway endpoint, using the enrollment code as the SMTP username and your svcpass (`UNITYSVC_API_KEY`) as the SMTP password.

## How it resolves

For an inbound SMTP request, the gateway uses the enrollment code from the username to find the row, reads `host`/`port`/`username` directly off the row, and resolves `${ customer_secrets.{{ params.password_secret }} ?? }` against the customer-secrets store to get the password. Then it makes the upstream SMTP connection.

The same service template supports unlimited SMTP configurations because every enrollment carries its own full upstream-config + password-secret name.

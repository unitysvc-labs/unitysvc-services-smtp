# SMTP Relay (Multi-Enrollment) — `labs/smtp-relay-plus`

Send email through **multiple** customer-owned SMTP servers under a single UnitySVC account. One enrollment per upstream SMTP (e.g. personal Gmail, work SendGrid, transactional SES). Pricing: **$1 per 1,000 emails** (1,000 emails per dollar).

If you only need **one** SMTP upstream, use the free `smtp-relay` (BYOK) service instead — this `-plus` variant exists for the multi-account case.

## Enrollment parameters

Each enrollment carries the upstream configuration as **direct parameters** at enroll time. Only the password is stored as a customer secret (named by `password_secret` so you can rotate it without re-enrolling).

| Parameter | Type | Required | Default | Meaning |
|---|---|---|---|---|
| `host` | string | optional | `mailpit.svcmarket.com` | SMTP hostname. The default points at the platform's mailpit sink so a no-config enrollment Just Works™ for testing. |
| `port` | integer | optional | `1025` | SMTP port. `1025` for mailpit, `587` for STARTTLS, `465` for TLS. |
| `username` | string | optional | `""` | SMTP username. Empty for mailpit (no auth). Usually your sending address or API username for real providers. |
| `password_secret` | string | optional | `""` | **Name** of the customer secret holding the SMTP password. The secret value is resolved at request time so rotation = one `usvc_seller secrets set` (no re-enroll). Leave empty for mailpit. |

The defaults are deliberately the **mailpit testing sink** — you can enroll with no params at all, send a test email immediately, and only set real values when wiring up production.

## 1. Pick the upstream SMTP

For each upstream you want to enroll, write down:

- **host** (e.g. `smtp.gmail.com`, `smtp.sendgrid.net`, `email-smtp.us-east-1.amazonaws.com`)
- **port** (`587` for STARTTLS, `465` for TLS)
- **username** (usually your email address or an API username)
- **password** (an app-password or API key — this is the only piece that goes to the secrets store)

## 2. Save each upstream's password as a customer secret

One secret per upstream. Use distinct names so each enrollment can point at the right one:

```bash
# Personal Gmail
usvc_seller secrets set GMAIL_SMTP_PASSWORD --value "<gmail-app-password>"

# Work SendGrid
usvc_seller secrets set SENDGRID_SMTP_PASSWORD --value "<sendgrid-api-key>"
```

The host/port/username are **not** secrets — they're parameters at enroll time. Only the password is sensitive enough to merit the secrets store.

## 3. Enroll, one per upstream

Each enrollment payload supplies the upstream's host/port/username inline and names its password secret. The platform issues a 6-character enrollment code per row.

```json
// Gmail enrollment
{
  "host": "smtp.gmail.com",
  "port": 587,
  "username": "you@gmail.com",
  "password_secret": "GMAIL_SMTP_PASSWORD"
}
```

```json
// SendGrid enrollment
{
  "host": "smtp.sendgrid.net",
  "port": 587,
  "username": "apikey",
  "password_secret": "SENDGRID_SMTP_PASSWORD"
}
```

```json
// Mailpit testing enrollment — defaults are fine, send empty
{}
```

## 4. Send mail through the gateway

The **username** at the gateway is the enrollment code; the **password** at the gateway is your UnitySVC svcpass (`UNITYSVC_API_KEY`). The gateway then resolves that enrollment's `host`/`port`/`username` + the customer secret named by `password_secret` and forwards to the upstream.

```python
import smtplib, os
from email.message import EmailMessage

msg = EmailMessage()
msg["From"] = "you@gmail.com"
msg["To"]   = "friend@example.com"
msg["Subject"] = "Hello from labs/smtp-relay-plus"
msg.set_content("Routed through my personal Gmail enrollment.")

with smtplib.SMTP(os.environ["SMTP_GATEWAY_HOST"], int(os.environ["SMTP_GATEWAY_PORT"])) as s:
    s.starttls()
    s.login("XXXXXX", os.environ["UNITYSVC_API_KEY"])  # enrollment code as username
    s.send_message(msg)
```

Switching upstreams is a one-character change in the SMTP username.

## 5. Rotating an upstream's password

Just overwrite the named secret:

```bash
usvc_seller secrets set GMAIL_SMTP_PASSWORD --value "<new-app-password>"
```

The next email through that enrollment picks the new value up immediately. No re-enroll needed.

## Troubleshooting

- **Gateway accepts login but upstream rejects** — wrong `username`, wrong `password_secret` name, or stale value in the named secret. The host/port/username are on the enrollment row; the password is the named secret — confirm both.
- **Connecting to mailpit by accident** — you enrolled with defaults; supply explicit `host`/`port`/`username`/`password_secret` to point at a real SMTP.
- **Sending limited / throttled** — that's an upstream-side limit (Gmail / SendGrid quota); not a gateway issue.
- **`tls: false` for STARTTLS providers** — the current offering pins `tls: false`; the gateway STARTTLS-upgrades inside the connection for ports 587/465. Open an issue if you have an upstream that needs an explicit TLS mode.

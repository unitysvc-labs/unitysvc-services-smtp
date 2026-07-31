## SMTP Relay — Bring Your Own Key

Send email through the UnitySVC SMTP gateway using **your own** SMTP server (Gmail, SendGrid, Mailgun, Amazon SES, etc.). You bring the SMTP credentials; the gateway authenticates your call with your svcpass key, resolves which upstream SMTP server to forward to, and relays the message — taking no commission on the mail itself, since it lands on your own server.

### How it works

The only thing that changes between the two usage methods below is **where the gateway gets your SMTP host / port / username / password from** — stored customer secrets, or per-enrollment parameters. Everything else (gateway authentication via svcpass, the upstream SMTP connection) is identical.

### Two ways to use this service

This service exposes two **upstream access channels**. Pick whichever fits — you can use both.

| | `byok` — stored SMTP server | `plus` — per-enrollment SMTP servers |
|---|---|---|
| Best for | one fixed SMTP upstream | many SMTP upstreams under one account |
| Host / port / user | `SMTP_RELAY_*` customer secrets | `host` / `port` / `username` parameters per enrollment |
| Password | `SMTP_RELAY_PASSWORD` customer secret | the secret named by the `password_secret` parameter |
| Reached at | the canonical gateway address (SMTP user `smtp-byok`) | a unique `/e/<code>` address per enrollment (SMTP user = enrollment code) |
| Price | **free** | **$0.001 / email** ($1 per 1,000) |

In both channels you authenticate to the gateway the same way: the **SMTP password is your svcpass** (`UNITYSVC_API_KEY`). The **SMTP username** is what selects the channel/route.

#### Method 1 — Stored SMTP server (`byok`, free)

One upstream SMTP, configured once via customer secrets.

1. **Provide your SMTP credentials** as customer secrets:
   - `SMTP_RELAY_HOST` — your SMTP hostname (e.g. `smtp.gmail.com`, `smtp.sendgrid.net`)
   - `SMTP_RELAY_USERNAME` — your SMTP username or sending address
   - `SMTP_RELAY_PASSWORD` — your SMTP password or app-specific password
   - `SMTP_RELAY_PORT` — *(optional)* SMTP port. Defaults to `587` (STARTTLS); set `465` for SMTPS.
   - `SMTP_RELAY_TLS` — *(optional)* whether to issue STARTTLS. Defaults to `true`; set `false` only for a local sink that doesn't speak TLS (e.g. `mailpit`).
2. **Send email** to the gateway with SMTP username `smtp-byok` and your svcpass as the password. The gateway resolves your upstream from the stored secrets and relays the message.

Common providers (all standard PLAIN/LOGIN SMTP): Gmail `smtp.gmail.com:587` (app password), SendGrid `smtp.sendgrid.net:587`, Mailgun `smtp.mailgun.org:587`, Amazon SES `email-smtp.us-east-1.amazonaws.com:587`, Postmark `smtp.postmarkapp.com:587`.

#### Method 2 — Per-enrollment SMTP servers (`plus`, metered)

Run **multiple** relays under one account — each enrollment routes to a different SMTP server. Useful for:

- **Personal + Work**: one enrollment for Gmail, another for your company's SMTP.
- **Transactional + Marketing**: separate enrollments for SES (transactional) and Mailgun (marketing).
- **Multi-tenant**: a different SMTP server per client or project.

The non-secret pieces — `host`, `port`, `username` — are set **directly** as enrollment parameters, so you can tell enrollments apart at a glance. Only the password is sensitive: it's a customer secret whose *name* you pass as `password_secret`, resolved at request time (rotate the value without re-enrolling).

1. **Save each upstream's password as a customer secret**, using a name that makes the enrollment obvious:

   ```bash
   usvc_seller secrets set GMAIL_SMTP_PASSWORD    --value "<gmail-app-password>"
   usvc_seller secrets set SENDGRID_SMTP_PASSWORD --value "<sendgrid-api-key>"
   ```

2. **Enroll once per upstream**, supplying `host` / `port` / `username` inline and `password_secret` as the name from step 1:

   ```json
   // Gmail
   { "host": "smtp.gmail.com",    "port": 587, "username": "you@gmail.com", "tls": true, "password_secret": "GMAIL_SMTP_PASSWORD" }
   ```
   ```json
   // SendGrid
   { "host": "smtp.sendgrid.net", "port": 587, "username": "apikey",        "tls": true, "password_secret": "SENDGRID_SMTP_PASSWORD" }
   ```

   Enroll with no params at all and you land on the platform's mailpit test sink (`mailpit.svcmarket.com:1025`) — handy for a first smoke test.

3. **Send mail** to each enrollment's unique `/e/<code>` gateway address, using the **enrollment code as the SMTP username** and your svcpass as the SMTP password. Switching upstreams is a one-value change to the SMTP username.

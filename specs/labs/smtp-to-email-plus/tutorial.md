# Tutorial — `labs/smtp-to-email-plus`

Run several independent email-to-webhook routes under one UnitySVC account, each delivering the **faithful email envelope** to a different HTTP receiver. Pricing: **$1 per 1,000 emails**.

## 1. Stand up the receivers (one per route)

Decide on the routes you need. A common shape:

| Logical route | Destination |
|---|---|
| Sales inbox | `https://crm.example.com/inbound-mail` |
| Support inbox | `https://helpdesk.example.com/email-ingest` |
| Ops alerts | `https://oncall.example.com/page` |

Each can be anything that accepts `POST application/json`. Start with `https://echo.unitysvc.dev` to validate the flow, then point it at real handlers.

## 2. (Optional) Save the bearer tokens as customer secrets — one per receiver

```bash
usvc_seller secrets set CRM_API_KEY      --value "<crm-bearer>"
usvc_seller secrets set HELPDESK_API_KEY --value "<helpdesk-bearer>"
# Ops receiver is public — no secret to set.
```

The names are yours; you'll reference them as `api_key_secret` at enroll time. Skip this step for public receivers.

## 3. Enroll, one per route

Each enrollment takes the destination URL inline as `base_url` and (optionally) the name of the bearer-token secret:

```json
// Sales enrollment
{ "base_url": "https://crm.example.com/inbound-mail",      "api_key_secret": "CRM_API_KEY" }
```
```json
// Support enrollment
{ "base_url": "https://helpdesk.example.com/email-ingest", "api_key_secret": "HELPDESK_API_KEY" }
```
```json
// Ops enrollment (no auth)
{ "base_url": "https://oncall.example.com/page" }
```

Each enrollment returns its own **6-character code** — that's the SMTP username for *that* route.

## 4. Send mail through the right route

The username chooses which enrollment fires; the same svcpass authenticates every route.

```python
import smtplib, os
from email.message import EmailMessage

def send(enrollment_code: str, subject: str, body: str):
    msg = EmailMessage()
    msg["From"]    = "alice@example.com"
    msg["To"]      = "router@unitysvc.com"
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(os.environ["SMTP_GATEWAY_HOST"], int(os.environ["SMTP_GATEWAY_PORT"])) as s:
        s.starttls()
        s.login(enrollment_code, os.environ["UNITYSVC_API_KEY"])
        s.send_message(msg)

send("XXXXXX", "lead: Acme Corp",     "Asked for a demo …")   # → CRM
send("YYYYYY", "ticket: login broken", "User foo cannot …")    # → Helpdesk
send("ZZZZZZ", "ALERT: api down",      "p99 > 5s for 10m …")   # → Ops
```

## 5. Verify via the platform

```bash
usvc_seller services run-tests labs/smtp-to-email-plus --force
```

Runs the gateway-side test against the `ops_testing_parameters` declared on the listing (`base_url: https://echo.unitysvc.dev`, `api_key_secret: HTTP_RELAY_API_KEY`). Add `--id <prefix>` if the run targets a specific enrollment row.

## Updating, rotating, decommissioning

- **Rotate a receiver's bearer token**: `usvc_seller secrets set <SECRET_NAME> --value <new-token>` — the next email picks it up. No re-enroll.
- **Move a route to a new URL**: re-enroll (or update the enrollment) with the new `base_url`. Existing email already sent through the old code is unaffected.
- **Retire a route**: withdraw the enrollment.

## Troubleshooting

- **All emails delivered to the same receiver** — you used the wrong enrollment code as the SMTP username. Each route has its own.
- **One route 401s, others work** — `api_key_secret` for that enrollment doesn't match what the receiver expects, or the secret value is stale. Re-set it.
- **Email sends OK to gateway, never arrives at receiver** — confirm the `base_url` of *that* enrollment, not just any enrollment. `usvc_seller services list` to inspect each enrollment row.

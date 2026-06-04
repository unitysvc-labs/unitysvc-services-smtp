# Tutorial — `labs/smtp-to-msg-plus`

Run several independent email-to-Apprise routes under one UnitySVC account. Each enrollment delivers the strict `{title, body, type, format}` envelope to a different Apprise-compatible receiver. Pricing: **$1 per 1,000 emails**.

## 1. Pick the receivers (one per route)

A typical pattern: one Apprise instance per "audience" of channels.

| Route | Receiver |
|---|---|
| Sales notifications → CRM-watchers' Slack | `https://apprise-sales.example.com/notify` |
| Ops alerts → on-call Discord + ntfy | `https://apprise-ops.example.com/notify` |
| Marketing campaigns → public broadcast | `https://apprise.unitysvc.dev/notify/<key>` |

Each receiver's per-channel destinations (Slack webhook, Discord URL, etc.) are configured **inside** that Apprise instance — not in UnitySVC. Use this service to route the email to the right Apprise instance; let Apprise handle the channel fan-out.

## 2. (Optional) Save the bearer tokens — one per receiver

```bash
usvc_seller secrets set APPRISE_SALES_KEY --value "<bearer>"
usvc_seller secrets set APPRISE_OPS_KEY   --value "<bearer>"
# Marketing receiver is public — no secret to set.
```

## 3. Enroll, one per route

```json
{ "base_url": "https://apprise-sales.example.com/notify",   "api_key_secret": "APPRISE_SALES_KEY" }
```
```json
{ "base_url": "https://apprise-ops.example.com/notify",     "api_key_secret": "APPRISE_OPS_KEY" }
```
```json
{ "base_url": "https://apprise.unitysvc.dev/notify/<key>" }
```

Each enrollment returns its own **6-character code**.

## 4. Send mail through the right route

```python
import smtplib, os
from email.message import EmailMessage

def notify(enrollment_code: str, subject: str, body: str):
    msg = EmailMessage()
    msg["From"]    = "alerts@example.com"
    msg["To"]      = "router@unitysvc.com"
    msg["Subject"] = subject     # → title
    msg.set_content(body)        # → body
    with smtplib.SMTP(os.environ["SMTP_GATEWAY_HOST"], int(os.environ["SMTP_GATEWAY_PORT"])) as s:
        s.starttls()
        s.login(enrollment_code, os.environ["UNITYSVC_API_KEY"])
        s.send_message(msg)

notify("XXXXXX", "lead: Acme Corp",       "asked for demo …")    # → sales Apprise
notify("YYYYYY", "ALERT: checkout p99>5s", "see grafana …")       # → ops Apprise
notify("ZZZZZZ", "blog: spring promo",     "live now …")          # → marketing Apprise
```

The same email body shape works for every route — the receiver decides how to channel-fan-out.

## 5. Verify via the platform

```bash
usvc_seller services run-tests labs/smtp-to-msg-plus --force
```

## Updating, rotating, decommissioning

- **Rotate** a receiver's bearer: `usvc_seller secrets set <SECRET_NAME> --value <new>` — next email picks it up.
- **Re-point** a route: update / re-enroll with a new `base_url`. The enrollment code stays the same if you update in place.
- **Retire** a route: withdraw that enrollment; other routes are unaffected.

## Troubleshooting

- **Wrong channel fires** — that's a config inside your Apprise instance, not at the gateway. The gateway just delivers the JSON.
- **`base_url` looks right but no notification arrives** — confirm your Apprise instance accepts the `/notify` shape used by `apprise-api` (`{title, body, type, format}`). Older apprise builds use different paths.

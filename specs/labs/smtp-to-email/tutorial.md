# Tutorial — `smtp-to-email`

End-to-end: stand up an HTTP receiver, save the secret, send a test email through the gateway, watch your receiver get it.

## 1. Stand up an HTTP endpoint that accepts JSON

Anything that speaks `POST application/json` works. For a quick smoke-test, you can use a free public receiver like `https://echo.unitysvc.dev` (echoes the body back) — useful for confirming the flow before pointing it at real code.

For a real integration, expose any handler. A minimal Python (FastAPI) example:

```python
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/inbound-mail")
async def inbound(req: Request):
    body = await req.json()
    print("from:", body["from"], "subject:", body["subject"])
    return {"ok": True}
```

Run it behind a public TLS URL (Cloudflare Tunnel, ngrok, your own LB, etc.).

## 2. Save the URL as a customer secret

```bash
usvc_seller secrets set HTTP_RELAY_BASE_URL --value "https://hooks.example.com/inbound-mail"
```

If your receiver needs `Authorization: Bearer …`, also:

```bash
usvc_seller secrets set HTTP_RELAY_API_KEY --value "<your-bearer-token>"
```

(Omit `HTTP_RELAY_API_KEY` entirely when the receiver is public.)

## 3. Send a test email through the gateway

Use any SMTP client. **Username = `smtp-to-email`**, **password = your svcpass** (`UNITYSVC_API_KEY`):

```python
import smtplib, os
from email.message import EmailMessage

msg = EmailMessage()
msg["From"]    = "alice@example.com"
msg["To"]      = "router@unitysvc.com"      # any address — routing is by SMTP user
msg["Subject"] = "hello from smtp-to-email"
msg.set_content("If you can see this in your HTTP receiver, the bridge works.")

with smtplib.SMTP(os.environ["SMTP_GATEWAY_HOST"], int(os.environ["SMTP_GATEWAY_PORT"])) as s:
    s.starttls()
    s.login("smtp-to-email", os.environ["UNITYSVC_API_KEY"])
    s.send_message(msg)
```

Within a second or two your receiver should print the email envelope.

## 4. Inspect the payload your receiver gets

A typical POST body:

```json
{
  "from":    "alice@example.com",
  "to":      ["router@unitysvc.com"],
  "subject": "hello from smtp-to-email",
  "date":    "2026-06-04T12:00:00Z",
  "text_body": "If you can see this in your HTTP receiver, the bridge works.\n",
  "html_body": null,
  "headers": [["Subject", "hello from smtp-to-email"], …],
  "attachments": [],
  "spf":   "pass",
  "dkim":  "pass",
  "dmarc": "pass"
}
```

Everything in the email is preserved. If you'd rather receive `{title, body, type, format}` instead (the Apprise-style notification envelope), switch to the `smtp-to-msg` service.

## 5. Verify via the platform

```bash
usvc_seller services run-tests smtp-to-email --force
```

This routes a synthetic test email through the gateway end-to-end (svcpass → routing → upstream POST) and reports each document's status.

## Troubleshooting

- **No POST arrives** — confirm `HTTP_RELAY_BASE_URL` is set (`usvc_seller secrets list`); confirm your receiver is publicly reachable; confirm the SMTP login succeeded (the gateway returns a clean `250` only after a valid svcpass auth).
- **POST arrives, receiver 401s** — `HTTP_RELAY_API_KEY` mismatch or missing; check the secret value, and that your receiver expects `Authorization: Bearer`.
- **Attachments missing** — they're in `attachments[].content` as base64; some clients display only `text_body`/`html_body`.
- **SMTP authentication fails** — confirm `UNITYSVC_API_KEY` is your seller svcpass, not a customer key from elsewhere.

# Tutorial — `smtp-to-msg`

End-to-end: stand up an Apprise-compatible receiver, save the secret, send a test email through the gateway, watch a notification fire.

## 1. Stand up an Apprise-style receiver

Anything that accepts `POST application/json` with `{title, body, type, format}` works. Two quick options:

- **Run [apprise-api](https://github.com/caronc/apprise-api) yourself** — `docker run -p 8000:8000 caronc/apprise:latest`. Endpoint: `http://your-host:8000/notify`.
- **Use the public `apprise.unitysvc.dev`** — a hosted Apprise instance maintained by UnitySVC. Endpoint: `https://apprise.unitysvc.dev/notify/<key>`.
- **Quick smoke-test only**: `https://echo.unitysvc.dev` echoes the body back so you can confirm the JSON shape.

Any of these accepts the exact envelope this service produces.

## 2. Save the receiver URL as a customer secret

```bash
usvc_seller secrets set HTTP_RELAY_BASE_URL --value "https://apprise.unitysvc.dev/notify/<key>"
```

If your receiver gates on a bearer token, also:

```bash
usvc_seller secrets set HTTP_RELAY_API_KEY --value "<bearer>"
```

## 3. Send a test email through the gateway

The username is the literal `smtp-to-msg`; the password is your svcpass:

```python
import smtplib, os
from email.message import EmailMessage

msg = EmailMessage()
msg["From"]    = "alerts@example.com"
msg["To"]      = "router@unitysvc.com"
msg["Subject"] = "p99 latency over 5s"        # → "title"
msg.set_content("checkout-api p99 = 6.4s for 10m; on-call paged.")  # → "body"

with smtplib.SMTP(os.environ["SMTP_GATEWAY_HOST"], int(os.environ["SMTP_GATEWAY_PORT"])) as s:
    s.starttls()
    s.login("smtp-to-msg", os.environ["UNITYSVC_API_KEY"])
    s.send_message(msg)
```

## 4. Verify the payload

Your receiver gets:

```json
{
  "title":  "p99 latency over 5s",
  "body":   "checkout-api p99 = 6.4s for 10m; on-call paged.",
  "type":   "info",
  "format": "text"
}
```

Plug that into apprise-api with destinations like `discord://…` / `tgram://…` / `ntfy://…` and the same email reaches whichever channels your apprise config targets.

## 5. Verify via the platform

```bash
usvc_seller services run-tests smtp-to-msg --force
```

## When to switch

- Want **attachments / full email**? Switch to the `smtp-to-email` service.
- Want **multiple receivers** (e.g. sales/support/ops each on a different apprise instance)? Switch to the paid `labs/smtp-to-msg-plus` service.

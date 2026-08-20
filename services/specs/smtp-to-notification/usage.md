# How to use the SMTP-to-Notification bridge

Send an email; every destination in your `/b/notification` group receives it.
There is nothing to enroll and nothing to configure — the upstream is fixed to
your own notification group.

## Prerequisite: a `/b/notification` group

This service delivers into the broadcast group named `notification` that belongs
to **you**. Notification delivery is opt-in, so if you have never set it up, the
group does not exist yet and sends will fail with a message telling you so.

Create it from the **Notifications** settings panel and add at least one
destination (`msg-to-email`, `msg-to-discord`, `msg-to-ntfy`, …). Everything you
add there is reached by this service automatically — you never touch this
service's configuration again.

## Sending

Authenticate to the SMTP gateway and send a normal email:

| Setting | Value |
|---|---|
| Host | your gateway's SMTP host |
| Username | `smtp-to-notification` |
| Password | your UnitySVC API key (`svcpass_…`) |

```bash
swaks --server "$SMTP_GATEWAY_HOST" \
      --auth-user smtp-to-notification \
      --auth-password "$UNITYSVC_API_KEY" \
      --to notify@svcmarket.com \
      --header "Subject: Backup finished" \
      --body "Nightly backup completed in 4m12s."
```

The subject becomes the notification **title** and the body becomes the
notification **body**.

## What gets delivered

The email is converted to the standard `{title, body, type, format}` envelope
before fan-out. That envelope is deliberately compact: **attachments, HTML
formatting, and custom headers are dropped**. If you need the full message
preserved, use `smtp-to-http` (faithful envelope to your own receiver) or add an
SMTP relay to the `/b/smtp-notification` group instead.

## Two ways to trigger the same group

| Your sender speaks | Use |
|---|---|
| HTTP | `POST` the envelope to `/b/notification` directly |
| SMTP | this service |

Both reach the same group and the same destinations.

## Adding an SMTP relay as well

This service is HTTP-only fan-out: it reaches notification channels, not mail
servers. To deliver a faithful copy to a real SMTP relay *and* notify your
channels, send to the `/b/smtp-notification` group — it holds your relay legs
alongside this bridge.

## Billing

The ingress hop is **free**. Each downstream notification channel bills on its
own listing, so one email costs whatever its destinations cost.

## Credential handling

The gateway replays your own API key on the internal hop to `/b/notification`.
The destination is fixed to a platform route and is not customer-configurable,
so the credential does not leave UnitySVC.

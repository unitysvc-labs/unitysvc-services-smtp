# UnitySVC Services - SMTP

This repository hosts SMTP relay service data for the UnitySVC platform.

## Services

Each service is **multi-channel**: a free `byok` channel (one upstream configured once
via customer secrets) and a metered `plus` channel (per-enrollment upstreams, reached at
`/e/<code>`, $1 per 1,000 emails).

### smtp-relay

Bring-your-own-key SMTP relay — send email through your own SMTP server (Gmail, SendGrid,
SES, …). `byok`: one SMTP server via `SMTP_RELAY_*` secrets. `plus`: many SMTP servers, one
per enrollment.

### smtp-to-email

SMTP-to-Email bridge — forwards inbound email to your HTTP endpoint as the faithful,
lossless email envelope. `byok`: one receiver via `HTTP_RELAY_BASE_URL`. `plus`: many
email-to-webhook routes, one per enrollment.

### smtp-to-msg

SMTP-to-Message bridge — forwards inbound email to your HTTP endpoint as the strict
`{title, body, type, format}` Apprise notification envelope. `byok`: one receiver via
`HTTP_RELAY_BASE_URL`. `plus`: many Apprise receivers, one per enrollment.

## Setup

```bash
pip install unitysvc-services
usvc data validate
usvc data run-tests
```

See [unitysvc-services documentation](https://github.com/unitysvc/unitysvc-services) for details.

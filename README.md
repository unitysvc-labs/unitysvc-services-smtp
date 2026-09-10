# UnitySVC Services - SMTP

This repository hosts SMTP relay service data for the UnitySVC platform.

## Services

Most relay services are **multi-channel**: a free `byok` channel (one upstream
configured once via customer secrets) and a metered `plus` channel
(per-enrollment upstreams, reached at `/e/<code>`, $1 per 1,000 emails).
Gateway-native bridge services can also be single-channel and require no
customer configuration.

### smtp-relay

Bring-your-own-key SMTP relay — send email through your own SMTP server (Gmail, SendGrid,
SES, …). `byok`: one SMTP server via `SMTP_RELAY_*` secrets. `plus`: many SMTP servers, one
per enrollment.

### smtp-to-http

SMTP-to-HTTP bridge — forwards inbound email to your HTTP endpoint as the faithful,
lossless email envelope. `byok`: one receiver via `SMTP_HTTP_RELAY_BASE_URL`. `plus`: many
email-to-webhook routes, one per enrollment.

### smtp-to-msg

SMTP-to-Message bridge — forwards inbound email to your HTTP endpoint as the strict
`{title, body, type, format}` Apprise notification envelope. `byok`: one receiver via
`SMTP_HTTP_RELAY_BASE_URL`. `plus`: many Apprise receivers, one per enrollment.

### smtp-to-api-gateway

SMTP-to-API-Gateway bridge — forwards inbound email into a route on the UnitySVC
API Gateway (a service, `a/<alias>`, `b/<group>`, `e/<code>`) as the caller's own
identity, as either the faithful `email` envelope or the compact `apprise`
envelope. `default`: one route via `SMTP_TO_API_GATEWAY_TARGET` /
`SMTP_TO_API_GATEWAY_FORMAT` (defaults `notify` / `apprise`, so it works with no
configuration). `plus`: many routes, one per enrollment.

### smtp-to-mailbox

SMTP-to-Mailbox bridge — forwards inbound email through UnitySVC's managed SMTP
upstream to the caller's verified primary email address. No enrollment or
per-service configuration is required.

## Setup

```bash
pip install unitysvc-services
usvc data validate
usvc data run-tests
```

See [unitysvc-services documentation](https://github.com/unitysvc/unitysvc-services) for details.

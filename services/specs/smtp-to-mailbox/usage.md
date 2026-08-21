# How to use SMTP-to-Mailbox

Send an email; UnitySVC delivers it to the verified primary email address on
your account. There is nothing to enroll and nothing to configure.

## Prerequisite: primary email

This service delivers to your `__PRIMARY_EMAIL` customer secret. UnitySVC sets
that secret from your verified account email. If it is missing, delivery fails
closed instead of accepting mail with an unknown destination.

## Sending

Authenticate to the SMTP gateway and send a normal email:

| Setting | Value |
|---|---|
| Host | your gateway's SMTP host |
| Username | `smtp-to-mailbox` |
| Password | your UnitySVC API key (`svcpass_...`) |

```bash
swaks --server "$SMTP_GATEWAY_HOST" \
      --auth-user smtp-to-mailbox \
      --auth-password "$UNITYSVC_API_KEY" \
      --to mailbox@svcmarket.com \
      --header "Subject: Gateway test" \
      --body "This message will be delivered to my verified primary email."
```

The gateway uses the `--to` address to accept a normal SMTP transaction, but the
upstream recipient is pinned to your `__PRIMARY_EMAIL`. Changing the envelope or
message recipient does not route mail to a different external address.

## What gets delivered

The full SMTP message is relayed through UnitySVC's managed svcpass.com SMTP
upstream. Subject, text body, HTML body, headers, and attachments are preserved
by the SMTP relay path.

## Billing

This service is free. It uses UnitySVC-managed mailbox delivery and does not
require a separate enrollment.

## Credential handling

Your UnitySVC API key authenticates only to the SMTP gateway. The managed SMTP
upstream credential is provided by the seller and is not visible to customers.

"""
Algorithm: Resolve test environment for upstream (local) testing.

Used by `usvc data run-tests` to build env vars for test script execution.
The test connects directly to the upstream service (no gateway).

Inputs:
  - offering.upstream_access_config: dict[str, dict]
    (each channel's params.testing_defaults supplies its Jinja2 params)
  - listing.service_options.enrollment_vars: dict[str, str]  (rendered enrollment vars)
  - listing.service_options.routing_vars: dict[str, str]  (seller operational vars)
  - os.environ: environment variables (used to resolve secrets)

Template context (matching request-time rendering):
  { enrollment_vars, params, routing_vars }
  (path.* is not available in local testing)
"""

import os
import re
from jinja2 import Template

SECRET_REF_RE = re.compile(r"^\$\{\s*(secrets|customer_secrets)\.(\w+)\s*\}")


def resolve_value(val: str, template_ctx: dict) -> str:
    """Expand Jinja2 templates then resolve secret references from env vars."""
    # Step 1: Expand Jinja2 templates
    # e.g. "{{ routing_vars.backend_host }}/api"
    # e.g. "${ customer_secrets.{{ params.SMTP_HOST_SECRET }} }"
    if "{{" in val:
        val = Template(val).render(**template_ctx)

    # Step 2: Resolve ${ secrets.NAME } / ${ customer_secrets.NAME } from env
    match = SECRET_REF_RE.match(val)
    if match:
        val = os.environ.get(match.group(2), "")

    return val


def resolve_upstream_test_context(
    upstream_access_config: dict[str, dict],
    enrollment_vars: dict[str, str] | None = None,
    routing_vars: dict[str, str] | None = None,
) -> dict[str, str]:
    """Build env vars for upstream local test execution."""
    env: dict[str, str] = {}

    for _upstream_name, config in upstream_access_config.items():
        if not isinstance(config, dict):
            continue

        # Build template context matching request-time rendering
        # (see docs/dev-notes/features/jinja2-template-system.md). Each
        # channel is tested with its own params.testing_defaults
        # (unitysvc/unitysvc#2726).
        channel_params = config.get("params") or {}
        template_ctx = {
            "params": channel_params.get("testing_defaults") or {},
            "enrollment_vars": enrollment_vars or {},
            "routing_vars": routing_vars or {},
        }

        for key, val in config.items():
            if key == "params":
                # The channel's parameter declaration, not a connection field.
                continue
            if key == "routing_key" and isinstance(val, dict):
                # Flatten routing_key dict: {"username": "foo"} -> USERNAME=foo
                for sub_key, sub_val in val.items():
                    env[sub_key.upper()] = str(sub_val)
            elif not isinstance(val, (str, int, float, bool)):
                # Skip complex types (dicts, lists, etc.)
                continue
            elif key == "base_url":
                env["SERVICE_BASE_URL"] = resolve_value(str(val), template_ctx)
            elif key == "api_key":
                env["UNITYSVC_API_KEY"] = resolve_value(str(val), template_ctx)
            else:
                env[key.upper()] = resolve_value(str(val), template_ctx)

    return env


# ---------------------------------------------------------------------------
# Examples
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    os.environ["SMTP_HOST"] = "smtp.gmail.com"
    os.environ["SMTP_PORT"] = "587"
    os.environ["SMTP_USERNAME"] = "user@gmail.com"
    os.environ["SMTP_PASSWORD"] = "app-password"

    # smtp-relay (byok channel)
    result = resolve_upstream_test_context({
        "Customer SMTP": {
            "access_method": "smtp",
            "host": "${ customer_secrets.SMTP_HOST }",
            "port": "${ customer_secrets.SMTP_PORT }",
            "username": "${ customer_secrets.SMTP_USERNAME }",
            "password": "${ customer_secrets.SMTP_PASSWORD }",
            "tls": True,
        }
    })
    print("=== smtp-relay (byok) ===")
    for k, v in sorted(result.items()):
        print(f"  {k}={v}")
    # ACCESS_METHOD=smtp, HOST=smtp.gmail.com, PASSWORD=app-password,
    # PORT=587, TLS=True, USERNAME=user@gmail.com

    # smtp-relay (parameterized + routing_key)
    result2 = resolve_upstream_test_context(
        upstream_access_config={
            "Customer SMTP": {
                "access_method": "smtp",
                "host": "${ customer_secrets.{{ params.SMTP_HOST_SECRET }} }",
                "port": "${ customer_secrets.{{ params.SMTP_PORT_SECRET }} }",
                "username": "${ customer_secrets.{{ params.SMTP_USERNAME_SECRET }} }",
                "password": "${ customer_secrets.{{ params.SMTP_PASSWORD_SECRET }} }",
                "tls": True,
                "routing_key": {"username": "my-relay"},
                "params": {
                    "schema": {"type": "object", "properties": {}},
                    "testing_defaults": {
                        "SMTP_HOST_SECRET": "SMTP_HOST",
                        "SMTP_PORT_SECRET": "SMTP_PORT",
                        "SMTP_USERNAME_SECRET": "SMTP_USERNAME",
                        "SMTP_PASSWORD_SECRET": "SMTP_PASSWORD",
                    },
                },
            }
        },
    )
    print("\n=== smtp-relay ===")
    for k, v in sorted(result2.items()):
        print(f"  {k}={v}")
    # ACCESS_METHOD=smtp, HOST=smtp.gmail.com, PASSWORD=app-password,
    # PORT=587, TLS=True, USERNAME=my-relay (from routing_key, overrides secret)

    # routing_vars example
    result3 = resolve_upstream_test_context(
        upstream_access_config={
            "upstream": {
                "base_url": "{{ routing_vars.backend_host }}/api/v1",
                "api_key": "${ secrets.API_KEY }",
            }
        },
        routing_vars={"backend_host": "https://prod.example.com"},
    )
    os.environ["API_KEY"] = "sk-test-123"
    result3 = resolve_upstream_test_context(
        upstream_access_config={
            "upstream": {
                "base_url": "{{ routing_vars.backend_host }}/api/v1",
                "api_key": "${ secrets.API_KEY }",
            }
        },
        routing_vars={"backend_host": "https://prod.example.com"},
    )
    print("\n=== routing_vars ===")
    for k, v in sorted(result3.items()):
        print(f"  {k}={v}")
    # SERVICE_BASE_URL=https://prod.example.com/api/v1
    # UNITYSVC_API_KEY=sk-test-123

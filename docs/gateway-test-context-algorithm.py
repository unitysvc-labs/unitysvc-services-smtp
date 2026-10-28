"""
Algorithm: Resolve test environment for gateway-based testing.

Used by `usvc services run-tests` (CLI) and celery approval tests.
The test connects through the gateway, not directly to upstream.

For each user_access_interface, only three types of values are exposed:
  - base_url      → SERVICE_BASE_URL
  - api_key       → UNITYSVC_API_KEY
  - routing_key   → flattened as KEY=value (uppercased)

All values are expanded with Jinja2 template rendering and secret resolution.

Inputs:
  - listing.user_access_interfaces: dict[str, dict]
  - the tested channel's params.testing_defaults: dict[str, str]
    (offering.upstream_access_config.<channel>.params.testing_defaults)
  - listing.service_options.enrollment_vars: dict[str, str] (rendered)
  - listing.service_options.routing_vars: dict[str, str]
  - gateway URL placeholders (e.g. ${SMTP_GATEWAY_BASE_URL})
  - ops customer API key
"""

import os
import re
from jinja2 import Template

SECRET_REF_RE = re.compile(r"^\$\{\s*(secrets|customer_secrets)\.(\w+)\s*\}")

# Gateway URL placeholders resolved from platform config
GATEWAY_URLS = {
    "${API_GATEWAY_BASE_URL}": os.environ.get("API_GATEWAY_BASE_URL", ""),
    "${S3_GATEWAY_BASE_URL}": os.environ.get("S3_GATEWAY_BASE_URL", ""),
    "${SMTP_GATEWAY_BASE_URL}": os.environ.get("SMTP_GATEWAY_BASE_URL", ""),
}


def resolve_value(val: str, template_ctx: dict) -> str:
    """Expand gateway placeholders, Jinja2 templates, and secret references."""
    # Step 1: Replace gateway URL placeholders
    for placeholder, url in GATEWAY_URLS.items():
        if placeholder in val:
            val = val.replace(placeholder, url)

    # Step 2: Expand Jinja2 templates
    if "{{" in val:
        val = Template(val).render(**template_ctx)

    # Step 3: Resolve ${ secrets.NAME } / ${ customer_secrets.NAME }
    match = SECRET_REF_RE.match(val)
    if match:
        val = os.environ.get(match.group(2), "")

    return val


def resolve_gateway_test_contexts(
    user_access_interfaces: dict[str, dict],
    ops_customer_api_key: str,
    testing_defaults: dict[str, str] | None = None,
    enrollment_vars: dict[str, str] | None = None,
    routing_vars: dict[str, str] | None = None,
) -> list[tuple[str, dict[str, str]]]:
    """Build env vars for each user_access_interface.

    Returns a list of (interface_name, env_dict) tuples.
    Each interface is tested independently.
    """
    template_ctx = {
        "params": testing_defaults or {},
        "enrollment_vars": enrollment_vars or {},
        "routing_vars": routing_vars or {},
    }

    results = []

    for iface_name, iface in user_access_interfaces.items():
        if not isinstance(iface, dict):
            continue

        env: dict[str, str] = {}

        # base_url → SERVICE_BASE_URL
        if "base_url" in iface:
            env["SERVICE_BASE_URL"] = resolve_value(str(iface["base_url"]), template_ctx)

        # api_key → UNITYSVC_API_KEY (or use ops customer API key)
        if "api_key" in iface:
            env["UNITYSVC_API_KEY"] = resolve_value(str(iface["api_key"]), template_ctx)
        else:
            env["UNITYSVC_API_KEY"] = ops_customer_api_key

        # routing_key → flatten as KEY=value
        routing_key = iface.get("routing_key")
        if isinstance(routing_key, dict):
            for rk_key, rk_val in routing_key.items():
                env[rk_key.upper()] = resolve_value(str(rk_val), template_ctx)

        results.append((iface_name, env))

    return results


# ---------------------------------------------------------------------------
# Examples
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    os.environ["SMTP_GATEWAY_BASE_URL"] = "smtp://smtp.staging.svcpass.com:587"
    OPS_API_KEY = "svcpass_labs_test_key"

    # test-mailpit: simple, no templates
    contexts = resolve_gateway_test_contexts(
        user_access_interfaces={
            "SMTP Gateway": {
                "access_method": "smtp",
                "base_url": "${SMTP_GATEWAY_BASE_URL}",
                "routing_key": {"username": "test-mailpit"},
            }
        },
        ops_customer_api_key=OPS_API_KEY,
    )
    print("=== test-mailpit ===")
    for name, env in contexts:
        print(f"  Interface: {name}")
        for k, v in sorted(env.items()):
            print(f"    {k}={v}")
    # SERVICE_BASE_URL=smtp://smtp.staging.svcpass.com:587
    # UNITYSVC_API_KEY=svcpass_labs_test_key
    # USERNAME=test-mailpit

    # smtp-relay: templated routing_key
    contexts2 = resolve_gateway_test_contexts(
        user_access_interfaces={
            "SMTP Gateway": {
                "access_method": "smtp",
                "base_url": "${SMTP_GATEWAY_BASE_URL}",
                "routing_key": {"username": "{{ enrollment_vars.code }}"},
            }
        },
        ops_customer_api_key=OPS_API_KEY,
        enrollment_vars={"code": "abc123"},
    )
    print("\n=== smtp-relay ===")
    for name, env in contexts2:
        print(f"  Interface: {name}")
        for k, v in sorted(env.items()):
            print(f"    {k}={v}")
    # SERVICE_BASE_URL=smtp://smtp.staging.svcpass.com:587
    # UNITYSVC_API_KEY=svcpass_labs_test_key
    # USERNAME=abc123

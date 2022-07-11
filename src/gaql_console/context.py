import os

from typing import NamedTuple


class GAQLContext(NamedTuple):
    client_customer_id: str
    client_id: str
    client_secret: str
    developer_token: str
    login_customer_id: str
    refresh_token: str


def from_envvars() -> GAQLContext:
    required = GAQLContext._fields
    collected = {}
    missing = set()

    for var_lowercase in required:
        var_uppercase = var_lowercase.upper()
        if var_uppercase not in os.environ:
            missing.add(var_lowercase)
        else:
            collected[var_lowercase] = os.environ[var_uppercase]

    if missing:
        missing_str = ", ".join(missing)
        raise ValueError(f"Required vars not set: {missing_str}", missing)

    return GAQLContext(**collected)

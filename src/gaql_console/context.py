import importlib
import os
import pathlib
import toml

from typing import NamedTuple, Mapping


class GAQLContext(NamedTuple):
    client_customer_id: str
    client_id: str
    client_secret: str
    developer_token: str
    login_customer_id: str
    refresh_token: str


def ensure_full_context(candidate: Mapping) -> GAQLContext:
    required = set(GAQLContext._fields)
    available = set(candidate.keys())
    missing = required.difference(available)
    if missing:
        missing_str = ", ".join(missing)
        raise ValueError(f"Missing following context values: {missing_str}", missing)
    return GAQLContext(**{k: str(v) for k, v in candidate.items()})


def parse_pyproject_toml() -> dict:
    # @TODO: try more locations
    location = pathlib.Path("pyproject.toml")
    if not location.is_file():
        raise ValueError(f"Unable to locate pyproject.toml under {location}")
    with location.open() as f:
        try:
            toml_data = toml.load(f)
            return toml_data["tool"]["gaql-console"]
        except KeyError:
            raise ValueError("No [tool.gaql-console] section in pyproject.toml.")


def from_anywhere(*args, **kwargs) -> GAQLContext:
    # @TODO: from argparse
    # @TODO: from pyproject.toml
    sources = (from_envvars, from_callable)
    for source in sources:
        try:
            return source(*args, **kwargs)
        except ValueError:
            pass
    sources_str = ", ".join(s.__name__ for s in sources)
    raise ValueError(f"Unable to populate valid GAQLContext. Used {sources_str}.")


def from_envvars(*args, **kwargs) -> GAQLContext:
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


def from_callable(*args, **kwargs) -> GAQLContext:
    toml_data = parse_pyproject_toml()
    context_callable = toml_data.get("context-callable")
    if not context_callable:
        raise ValueError("No context-callable under [tool.gaql-console]")

    module_name, callable_name = context_callable.split(":", maxsplit=1)

    # @TODO: better exception handling
    module = importlib.import_module(module_name)
    callable = getattr(module, callable_name)

    raw_context = callable(*args, **kwargs)
    return ensure_full_context(raw_context)

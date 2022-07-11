import importlib
import os
import pathlib
from typing import NamedTuple, Mapping

import toml

from gaql_console import exceptions


class GAQLContext(NamedTuple):
    client_customer_id: str
    client_id: str
    client_secret: str
    developer_token: str
    login_customer_id: str
    refresh_token: str


def ensure_full_context(candidate: Mapping, source: str) -> GAQLContext:
    required = set(GAQLContext._fields)
    available = set(candidate.keys())
    missing = required.difference(available)
    if missing:
        missing_str = ", ".join(missing)
        raise exceptions.ContextException(f"Following context values were missing in {source}: {missing_str}", missing)
    return GAQLContext(**{k: str(candidate[k]) for k in required})


def parse_pyproject_toml() -> dict:
    # @TODO: try more locations
    location = pathlib.Path("pyproject.toml")
    if not location.is_file():
        raise exceptions.ContextException(f"Unable to locate pyproject.toml under {location}")
    with location.open() as f:
        try:
            toml_data = toml.load(f)
            return toml_data["tool"]["gaql-console"]
        except KeyError:
            raise exceptions.ContextException("No [tool.gaql-console] section in pyproject.toml.")


def build_context(source: str, *args, **kwargs) -> GAQLContext:
    return CONTEXT_CHOICES[source](*args, **kwargs)


def from_anywhere(*args, **kwargs) -> GAQLContext:
    # @TODO: from argparse
    # @TODO: from pyproject.toml
    sources = (from_envvars, from_callable)
    inner_exceptions = []
    for source in sources:
        try:
            return source(*args, **kwargs)
        except exceptions.ContextException as exc:
            inner_exceptions.append(exc)
    sources_str = ", ".join(s.__name__ for s in sources)
    raise exceptions.ContextException(f"Unable to populate valid GAQLContext. Used {sources_str}.", inner_exceptions)


def from_envvars(*args, **kwargs) -> GAQLContext:
    prefix = "GAQL_"
    raw_context = {k.lstrip(prefix).lower(): os.environ[k] for k in os.environ if k.startswith(prefix)}
    return ensure_full_context(raw_context, "envvars")


def from_callable(*args, **kwargs) -> GAQLContext:
    toml_data = parse_pyproject_toml()
    context_callable = toml_data.get("context-callable")
    if not context_callable:
        raise exceptions.ContextException("No context-callable under [tool.gaql-console]")

    module_name, callable_name = context_callable.split(":", maxsplit=1)

    # @TODO: better exception handling
    module = importlib.import_module(module_name)
    callable = getattr(module, callable_name)

    raw_context = callable(*args, **kwargs)
    return ensure_full_context(raw_context, callable_name)


CONTEXT_CHOICES = {
    "anywhere": from_anywhere,
    "envvars": from_envvars,
    "callable": from_callable,
}

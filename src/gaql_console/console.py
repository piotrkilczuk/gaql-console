from os import environ
from sys import stderr

from click import secho
from prompt_toolkit import PromptSession
from prompt_toolkit.lexers import PygmentsLexer

from gaql_console import VERSION, context
from gaql_console.api_client import GAQLClient
from gaql_console.context import GAQLContext
from gaql_console.exceptions import QueryException, handle_console_errors
from gaql_console.grammar import GAQLLexer, GAQLCompleter


def error(message: str):
    secho(message=message, fg="red", file=stderr)


def info(message: str):
    secho(message=message, fg="blue", file=stderr)


def ensure_envvars_set() -> GAQLContext:
    all = True
    collected = {}

    for var_lowercase in GAQLContext._fields:
        var_uppercase = var_lowercase.upper()
        if var_uppercase not in environ:
            error(f"${var_uppercase} not set")
            all = False
        else:
            collected[var_lowercase] = environ[var_uppercase]

    if not all:
        raise ValueError("Necessary environment variables have not been set.")

    return GAQLContext(**collected)


@handle_console_errors()
def main():
    # @TODO: from callable
    # @TODO: from argparse
    # @TODO: from pyproject.toml
    ctx = context.from_envvars()

    session = PromptSession()

    version_str = ".".join([str(v) for v in VERSION])
    info(f"Welcome to GAQL Console v{version_str}.")
    info("Use [Alt+Enter] or [Esc+Enter] to submit. [^D] to quit.\n")

    while True:
        gaql = session.prompt(
            "GAQL> ",
            lexer=PygmentsLexer(GAQLLexer),
            completer=GAQLCompleter(),
            multiline=True,
            # @TODO: better key bindings
        ).strip()
        if not gaql:
            info("Empty GAQL query. Use [^D] to quit.\n")
            continue

        ads_client = GAQLClient(ctx)

        try:
            responses = ads_client.query(gaql)
            for response in responses:
                print(response)

        except QueryException as exc:
            error(exc.message)

        except KeyboardInterrupt:
            error("Response stream interrupted")
            continue

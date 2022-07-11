import sys
from typing import List, Tuple

import click
from prompt_toolkit.lexers import pygments
from prompt_toolkit import shortcuts

import gaql_console
from gaql_console import exceptions, context, grammar, api_client


def error(message: str):
    click.secho(message=message, fg="red", file=sys.stderr)


def info(message: str):
    click.secho(message=message, fg="blue", file=sys.stderr)


def parse_extra_args(extra_args: List[str]) -> Tuple[List[str], dict[str, str]]:
    args = []
    kwargs = {}
    for extra_arg in extra_args:
        if extra_arg.startswith("--"):
            name, value = extra_arg.lstrip("--").split("=", maxsplit=1)
            kwargs[name] = value
        else:
            args.append(extra_arg)
    return args, kwargs


@click.command(context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.pass_context
@exceptions.handle_console_errors()
def main(click_ctx: click.Context):
    args, kwargs = parse_extra_args(click_ctx.args)
    try:
        ctx = context.from_anywhere(*args, **kwargs)
    except ValueError as exc:
        error(str(exc))
        exit(1)

    session = shortcuts.PromptSession()

    version_str = ".".join([str(v) for v in gaql_console.VERSION])
    info(f"Welcome to GAQL Console v{version_str}.")
    info("Use [Alt+Enter] or [Esc+Enter] to submit. [^D] to quit.\n")

    while True:
        gaql = session.prompt(
            "GAQL> ",
            lexer=pygments.PygmentsLexer(grammar.GAQLLexer),
            completer=grammar.GAQLCompleter(),
            multiline=True,
            # @TODO: better key bindings
        ).strip()
        if not gaql:
            info("Empty GAQL query. Use [^D] to quit.\n")
            continue

        ads_client = api_client.GAQLClient(ctx)

        try:
            responses = ads_client.query(gaql)
            for response in responses:
                print(response)

        except exceptions.QueryException as exc:
            error(exc.message)

        except KeyboardInterrupt:
            error("Response stream interrupted")
            continue

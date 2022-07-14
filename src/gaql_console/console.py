import pathlib
import sys
import time
from typing import List, Tuple

import click
from prompt_toolkit.lexers import pygments
from prompt_toolkit import shortcuts, history

import gaql_console
from gaql_console import exceptions, context, grammar, api_client


class Timed:
    start: float
    end: float

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end = time.time()

    @property
    def elapsed(self) -> float:
        return self.end - self.start


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
@click.option("--context-source", type=click.Choice(context.CONTEXT_CHOICES), default="anywhere")
@click.option("--verbose", "-v", is_flag=True)
@click.pass_context
@exceptions.handle_console_errors()
def main(click_ctx: click.Context, context_source: str, verbose: bool = False):
    args, kwargs = parse_extra_args(click_ctx.args)
    try:
        ctx = context.build_context(context_source, *args, **kwargs)
    except exceptions.ContextException as exc:
        error(exc.message)
        if verbose:
            for inner_exc in exc.inner_exceptions:
                error(inner_exc.message)
        exit(1)

    history_file = pathlib.Path.home() / ".gaql_console"
    history_file.touch(0o600)
    session_history = history.FileHistory(str(history_file))

    session = shortcuts.PromptSession(history=session_history)

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
            with Timed() as t:
                responses = ads_client.query(gaql)
                for response in responses:
                    print(response)
            print(f"Took {t.elapsed:.3f} seconds\n")

        except exceptions.QueryException as exc:
            error(exc.message)

        except KeyboardInterrupt:
            error("Response stream interrupted")
            continue

import pathlib
import sys
import time
from typing import List, Tuple

import click
from prompt_toolkit.lexers import pygments
from prompt_toolkit import shortcuts, history

import gaql_console
from gaql_console import api_client, context, exceptions, grammar, output


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
@click.option("-c", "--command", "command", default=None, help="Execute a single GAQL query and exit, like psql -c.")
@click.pass_context
@exceptions.handle_console_errors()
def main(click_ctx: click.Context, context_source: str, verbose: bool = False, command: str = None):
    args, kwargs = parse_extra_args(click_ctx.args)
    try:
        ctx = context.build_context(context_source, *args, **kwargs)
    except exceptions.ContextException as exc:
        output.error(exc.message)
        if verbose:
            for inner_exc in exc.inner_exceptions:
                output.error(inner_exc.message)
        exit(1)

    ads_client = api_client.GAQLClient(ctx)

    if command is not None:
        try:
            for _, response in ads_client.query(command):
                print(response)
        except exceptions.QueryException as exc:
            output.error(exc.message)
            exit(1)
        return

    history_file = pathlib.Path.home() / ".gaql_console"
    history_file.touch(0o600)
    session_history = history.FileHistory(str(history_file))

    session = shortcuts.PromptSession(history=session_history)

    version_str = ".".join([str(v) for v in gaql_console.VERSION])
    output.info(f"Welcome to GAQL Console v{version_str}.")
    output.info("Use [Alt+Enter] or [Esc+Enter] to submit. [^D] to quit.\n")

    writable_stream: output.OutputStream = output.OutputStream.default()

    try:
        while True:
            gaql = session.prompt(
                "GAQL> ",
                lexer=pygments.PygmentsLexer(grammar.GAQLLexer),
                completer=grammar.GAQLCompleter(),
                multiline=True,
                # @TODO: better key bindings
            ).strip()

            if not gaql:
                output.info("Empty GAQL query. Use [^D] to quit.\n")
                continue
            if gaql.startswith("\\o"):
                writable_stream = output.OutputStream.resolve(gaql, writable_stream)
                continue

            try:
                with Timed() as t:
                    writable_stream.begin_query()
                    for field_mask, response in ads_client.query(gaql):
                        writable_stream.write_row(field_mask, response)
                if writable_stream.file is sys.stdout:
                    print(f"Took {t.elapsed:.3f} seconds\n")

            except exceptions.QueryException as exc:
                output.error(exc.message)

            except KeyboardInterrupt:
                output.error("Response stream interrupted")
                continue
    finally:
        writable_stream.close()

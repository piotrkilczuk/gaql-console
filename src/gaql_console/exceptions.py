from contextlib import contextmanager


@contextmanager
def handle_console_errors():
    try:
        yield
    except EOFError:
        exit(0)
    except KeyboardInterrupt:
        exit(1)


class QueryException(Exception):
    message: str

    def __init__(self, message: str):
        self.message = message

from __future__ import annotations

import contextlib
from typing import List, Optional


@contextlib.contextmanager
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


class ContextException(ValueError):
    message: str
    inner_exceptions: List[ContextException]

    def __init__(self, message: str, inner_exceptions: Optional[List[Exception]] = None):
        self.message = message
        self.inner_exceptions = inner_exceptions or []

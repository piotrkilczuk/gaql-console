from typing import Iterable

from prompt_toolkit.completion import WordCompleter, Completer, Completion, CompleteEvent
from prompt_toolkit.document import Document
from pygments.lexer import RegexLexer
from pygments.token import Whitespace, Keyword, Name, Operator, Punctuation

FUNCTIONS = {
    "LAST_14_DAYS",
    "LAST_30_DAYS",
    "LAST_7_DAYS",
    "LAST_BUSINESS_WEEK",
    "LAST_MONTH",
    "LAST_WEEK_MON_SUN",
    "LAST_WEEK_SUN_SAT",
    "THIS_MONTH",
    "THIS_WEEK_MON_TODAY",
    "THIS_WEEK_SUN_TODAY",
    "TODAY",
    "YESTERDAY",
}
# @TOOD: PARAMETERS clause - what is this for
KEYWORDS = {"SELECT", "FROM", "WHERE", "ORDER BY", "LIMIT", "ASC", "DESC", "AND"}
OPERATORS = {
    "IN",
    "NOT IN",
    "LIKE",
    "NOT LIKE",
    "CONTAINS ANY",
    "CONTAINS ALL",
    "CONTAINS NONE",
    "IS NULL",
    "IS NOT NULL",
    "DURING",
    "BETWEEN",
    "REGEXP_MATCH",
    "NOT REGEXP_MATCH",
}


class GAQLLexer(RegexLexer):
    """
    See: https://developers.google.com/google-ads/api/docs/query/grammar
    """

    name = "GAQL"
    aliases = ["gaql"]
    filenames = ["*.gaql"]

    function_tokens = [(f"(?i)({token})", Keyword) for token in FUNCTIONS]
    keyword_tokens = [(f"(?i)({token})", Keyword) for token in KEYWORDS]
    operator_tokens = [(f"(?i)({token})", Operator) for token in OPERATORS]

    tokens = {
        "root": [
            (r"\s+", Whitespace),
            (r",", Punctuation),
            *keyword_tokens,
            (r"(=|!=|>|>=|<|<=)", Operator),
            *operator_tokens,
            *function_tokens,
            (r"([\w.]+)", Name.Attribute),
        ],
    }


gaql_autocompleter = WordCompleter([*FUNCTIONS, *KEYWORDS, *OPERATORS], ignore_case=True)


class GAQLCompleter(Completer):
    def _complete_with_rewind(self, document: Document, word: str) -> Iterable[Completion]:
        words = document.text_before_cursor.rsplit(maxsplit=1)
        if not words:
            return

        final_word = words[-1].upper()

        len_final_word = len(final_word)
        if len_final_word == len(word):
            return
        if final_word == word[:len_final_word]:
            yield Completion(word, -len_final_word)

    def get_completions(self, document: Document, complete_event: CompleteEvent) -> Iterable[Completion]:
        text_before = document.text_before_cursor

        if "SELECT" not in text_before:
            yield from self._complete_with_rewind(document, "SELECT")

        # FROM must come after any fields
        # fields have to have a dot in the lookup path
        if "." in text_before and "FROM" not in text_before:
            yield from self._complete_with_rewind(document, "FROM")

        if "FROM" in text_before:
            yield from self._complete_with_rewind(document, "WHERE")
            yield from self._complete_with_rewind(document, "ORDER BY")
            yield from self._complete_with_rewind(document, "LIMIT")

from typing import Iterable

from prompt_toolkit import completion, document
from prompt_toolkit.completion import word_completer
from pygments import lexer, token

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


class GAQLLexer(lexer.RegexLexer):
    """
    See: https://developers.google.com/google-ads/api/docs/query/grammar
    """

    name = "GAQL"
    aliases = ["gaql"]
    filenames = ["*.gaql"]

    function_tokens = [(f"(?i)({t})", token.Keyword) for t in FUNCTIONS]
    keyword_tokens = [(f"(?i)({t})", token.Keyword) for t in KEYWORDS]
    operator_tokens = [(f"(?i)({t})", token.Operator) for t in OPERATORS]

    tokens = {
        "root": [
            (r"\s+", token.Whitespace),
            (r",", token.Punctuation),
            *keyword_tokens,
            (r"(=|!=|>|>=|<|<=)", token.Operator),
            *operator_tokens,
            *function_tokens,
            (r"([\w.]+)", token.Name.Attribute),
        ],
    }


gaql_autocompleter = word_completer.WordCompleter([*FUNCTIONS, *KEYWORDS, *OPERATORS], ignore_case=True)


class GAQLCompleter(completion.Completer):
    def _complete_with_rewind(self, document: document.Document, word: str) -> Iterable[completion.Completion]:
        words = document.text_before_cursor.rsplit(maxsplit=1)
        if not words:
            return

        final_word = words[-1].upper()

        len_final_word = len(final_word)
        if len_final_word == len(word):
            return
        if final_word == word[:len_final_word]:
            yield completion.Completion(word, -len_final_word)

    def get_completions(
        self, _document: document.Document, complete_event: completion.CompleteEvent
    ) -> Iterable[completion.Completion]:
        text_before = _document.text_before_cursor

        if "SELECT" not in text_before:
            yield from self._complete_with_rewind(_document, "SELECT")

        # FROM must come after any fields
        # fields have to have a dot in the lookup path
        if "." in text_before and "FROM" not in text_before:
            yield from self._complete_with_rewind(_document, "FROM")

        if "FROM" in text_before:
            yield from self._complete_with_rewind(_document, "WHERE")
            yield from self._complete_with_rewind(_document, "ORDER BY")
            yield from self._complete_with_rewind(_document, "LIMIT")

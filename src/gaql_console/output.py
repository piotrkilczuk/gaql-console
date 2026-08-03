from __future__ import annotations

import abc
import csv
import enum
import json
import pathlib
import sys
from typing import Dict, List, TextIO, Type

import click
from google.protobuf import field_mask_pb2

from gaql_console import api_client


def error(message: str) -> None:
    click.secho(message=message, fg="red", file=sys.stderr)


def info(message: str) -> None:
    click.secho(message=message, fg="blue", file=sys.stderr)


def extract_value(row: api_client.GoogleAdsRow, path: str) -> object:
    value: object = row
    for part in path.split("."):
        value = getattr(value, part)
    if isinstance(value, enum.Enum):
        return value.name
    if hasattr(value, "__len__") and not isinstance(value, str):
        return list(value)  # repeated fields -> plain list
    return value


def build_nested(paths: List[str], row: api_client.GoogleAdsRow) -> dict:
    nested: dict = {}
    for path in paths:
        *segments, leaf = path.split(".")
        target = nested
        for segment in segments:
            target = target.setdefault(segment, {})
        target[leaf] = extract_value(row, path)
    return nested


class OutputFormat(enum.Enum):
    TXT = "txt"
    JSON = "json"
    CSV = "csv"


EXTENSION_FORMATS: Dict[str, OutputFormat] = {
    ".csv": OutputFormat.CSV,
    ".json": OutputFormat.JSON,
    ".jsonl": OutputFormat.JSON,
}


def infer_format(filepath: str) -> OutputFormat:
    return EXTENSION_FORMATS.get(pathlib.Path(filepath).suffix, OutputFormat.TXT)


class OutputStream(abc.ABC):
    def __init__(self, file: TextIO) -> None:
        self.file: TextIO = file

    def begin_query(self) -> None:
        """Called once per query execution, before any rows are written."""

    @abc.abstractmethod
    def write_row(self, field_mask: field_mask_pb2.FieldMask, row: api_client.GoogleAdsRow) -> None:
        ...

    def close(self) -> None:
        if self.file is not sys.stdout:
            self.file.close()

    @classmethod
    def default(cls) -> "OutputStream":
        return TxtOutputStream(sys.stdout)

    @classmethod
    def resolve(cls, line: str, current: "OutputStream") -> "OutputStream":
        args = line.removeprefix("\\o").split()
        current.close()

        if not args:
            info("Output reset to stdout.")
            return cls.default()

        if len(args) == 1:
            (filepath,) = args
            fmt = infer_format(filepath)
        elif len(args) == 2:
            fmt_token, filepath = args
            try:
                fmt = OutputFormat(fmt_token.lower())
            except ValueError:
                error(f"Unknown output format: {fmt_token}")
                return current
        else:
            error("Usage: \\o [format] [filepath]")
            return current

        try:
            file = open(filepath, "w", newline=("" if fmt is OutputFormat.CSV else None))
        except OSError as exc:
            error(f"Could not open {filepath}: {exc}")
            return current

        info(f"Writing {fmt.value} output to {filepath}")
        return FORMAT_CLASSES[fmt](file)


class TxtOutputStream(OutputStream):
    def write_row(self, field_mask: field_mask_pb2.FieldMask, row: api_client.GoogleAdsRow) -> None:
        print(row, file=self.file)


class JsonOutputStream(OutputStream):
    def write_row(self, field_mask: field_mask_pb2.FieldMask, row: api_client.GoogleAdsRow) -> None:
        print(json.dumps(build_nested(list(field_mask.paths), row)), file=self.file)


class CsvOutputStream(OutputStream):
    def __init__(self, file: TextIO) -> None:
        super().__init__(file)
        self._header_written: bool = False

    def begin_query(self) -> None:
        self._header_written = False

    def write_row(self, field_mask: field_mask_pb2.FieldMask, row: api_client.GoogleAdsRow) -> None:
        writer = csv.writer(self.file)
        if not self._header_written:
            writer.writerow(field_mask.paths)
            self._header_written = True
        writer.writerow([extract_value(row, path) for path in field_mask.paths])



FORMAT_CLASSES: Dict[OutputFormat, Type[OutputStream]] = {
    OutputFormat.TXT: TxtOutputStream,
    OutputFormat.JSON: JsonOutputStream,
    OutputFormat.CSV: CsvOutputStream,
}

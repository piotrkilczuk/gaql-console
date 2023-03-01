import pathlib
from typing import Dict

import toml

import gaql_console


def read_pyproject_toml() -> Dict:
    with pathlib.Path("pyproject.toml").open() as f:
        toml_data = toml.load(f)
    return toml_data


def reconcile_versions():
    pyproject_toml_data = read_pyproject_toml()
    pyproject_toml_version = pyproject_toml_data["tool"]["poetry"]["version"]
    source_code_versions = ".".join(str(v) for v in gaql_console.VERSION)
    assert (
        pyproject_toml_version == source_code_versions
    ), "Version in pyproject.toml and __init__.py has to be the same"


def main():
    reconcile_versions()


if __name__ == "__main__":
    main()

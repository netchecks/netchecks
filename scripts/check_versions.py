#!/usr/bin/env python3

from pathlib import Path
import sys
import tomllib
import yaml


def read_toml(file: str) -> dict:
    with open(file, "rb") as f:
        return tomllib.load(f)


def read_yaml(file: str) -> dict:
    with open(file, "r") as f:
        return yaml.safe_load(f)


if __name__ == "__main__":
    git_root_path = Path(__file__).resolve().parent.parent
    cli_toml_path = git_root_path / "pyproject.toml"
    operator_toml_path = git_root_path / "operator" / "pyproject.toml"
    operator_chart_path = git_root_path / "operator" / "charts" / "netchecks" / "Chart.yaml"

    cli_toml = read_toml(cli_toml_path)
    operator_toml = read_toml(operator_toml_path)
    operator_chart_yaml = read_yaml(operator_chart_path)

    cli_version = cli_toml["project"]["version"]
    operator_version = operator_toml["tool"]["poetry"]["version"]
    operator_chart_version = operator_chart_yaml["appVersion"]

    if len(set((cli_version, operator_version, operator_chart_version))) == 1:
        print("Versions match!")
        sys.exit(0)
    else:
        print(
            f"Error: Versions do not match\n{cli_toml_path}: {cli_version}\n{operator_toml_path}: {operator_version}\n{operator_chart_path}: {operator_chart_version}",
            file=sys.stderr,
        )
        sys.exit(1)

"""Local browser preview studio assets."""

from pathlib import Path


def asset_folder() -> Path:
    return Path(__file__).resolve().parent

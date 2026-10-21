"""Helper that loads test data from the CSV files in automation/data."""
import csv
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def read_csv(name):
    """Return the rows of automation/data/<name> as a list of dicts."""
    with open(DATA_DIR / name, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def csv_params(name):
    """Build pytest.param objects with the case_id as the test id."""
    import pytest

    return [pytest.param(row, id=row["case_id"]) for row in read_csv(name)]

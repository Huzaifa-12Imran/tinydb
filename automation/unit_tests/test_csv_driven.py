"""
Task 3: data driven tests that read their data from external CSV files.

Owner: Huzaifa Imran and Musab Butt (one test each)

Data files (automation/data):
    query_cases.csv        Query comparison operators (ECP + BVA)
    lru_cases.csv          LRUCache eviction behaviour (BVA on capacity)
    cache_flush_cases.csv  CachingMiddleware flush threshold (BVA)
    freeze_cases.csv       freeze() type conversion (ECP)

To add a case, add a row to the CSV. No Python change is needed.
"""
import json
import operator

import pytest

from tinydb.middlewares import CachingMiddleware
from tinydb.queries import where
from tinydb.utils import LRUCache, freeze

from .csv_data import csv_params

pytestmark = pytest.mark.datadriven

OPERATORS = {
    "eq": operator.eq,
    "ne": operator.ne,
    "lt": operator.lt,
    "le": operator.le,
    "gt": operator.gt,
    "ge": operator.ge,
}


@pytest.mark.queries
@pytest.mark.parametrize("row", csv_params("query_cases.csv"))
def test_query_operator_from_csv(row):
    query = OPERATORS[row["operator"]](where(row["field"]), json.loads(row["rhs_json"]))
    document = json.loads(row["document_json"])
    assert bool(query(document)) is (row["expected"] == "true")


@pytest.mark.utils
@pytest.mark.parametrize("row", csv_params("lru_cases.csv"))
def test_lru_eviction_from_csv(row):
    capacity = int(row["capacity"]) if row["capacity"] else None
    cache = LRUCache(capacity)
    for key in row["keys"].split("|"):
        cache.set(key, True)
    expected = row["expected_lru"].split("|") if row["expected_lru"] else []
    assert cache.lru == expected


@pytest.mark.middleware
@pytest.mark.parametrize("row", csv_params("cache_flush_cases.csv"))
def test_cache_flush_threshold_from_csv(row, counting_storage_cls):
    middleware = CachingMiddleware(counting_storage_cls)()
    middleware.WRITE_CACHE_SIZE = int(row["write_cache_size"])
    for index in range(int(row["writes"])):
        middleware.write({"n": index})
    assert middleware.storage.write_count == int(row["expected_storage_writes"])


@pytest.mark.utils
@pytest.mark.parametrize("row", csv_params("freeze_cases.csv"))
def test_freeze_type_from_csv(row):
    frozen = freeze(json.loads(row["input_json"]))
    assert type(frozen).__name__ == row["expected_type"]
    if row["hashable"] == "true":
        hash(frozen)

# TinyDB unit test automation (Assignment 3)

Project under test: TinyDB (https://github.com/msiemens/tinydb), MIT license, pure Python.
Everything for the assignment lives in this `automation` folder. Nothing in the original `tinydb` package or its own `tests` folder is modified.

Modules under test
1. tinydb/utils.py        LRUCache, freeze, FrozenDict
2. tinydb/queries.py      Query, QueryInstance
3. tinydb/middlewares.py  Middleware, CachingMiddleware

## 1. Environment setup (Task 1)

Requirements: Python 3.9 or newer, git.

    git clone <your group repo url>
    cd tinydb

Windows (PowerShell):

    python -m venv .venv
    .venv\Scripts\Activate.ps1
    pip install -e .
    pip install -r automation\requirements-test.txt

Linux or macOS:

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -e .
    pip install -r automation/requirements-test.txt

Check:

    cd automation
    python -m pytest --version
    python -m pytest -q

Expected: all tests pass (239 at the time of writing).

## 2. Folder layout

    automation/
      pytest.ini               markers, strict mode, default test path
      conftest.py              execution order hook, CountingMemoryStorage fixture
      run_suites.py            runs the suites in a fixed order
      requirements-test.txt
      unit_tests/
        test_utils_lrucache.py     module 1, LRUCache
        test_utils_freeze.py       module 1, freeze and FrozenDict
        test_queries.py            module 2, Query
        test_middlewares.py        module 3, Middleware and CachingMiddleware
        test_csv_driven.py         Task 3, data driven tests
        csv_data.py                CSV loader
      data/
        query_cases.csv  lru_cases.csv  cache_flush_cases.csv  freeze_cases.csv
      docs/
        ECP_BVA_NOTES.md           test design notes (Task 2)
        TestCases.xlsx             test case sheet (Task 3)
      setup_video/                 put the screen recording here (Task 1)

## 3. Running tests (Task 4)

Run from the `automation` folder.

All tests, serial, in the configured order:

    python -m pytest

All tests in parallel (pytest-xdist, one file per worker):

    python -m pytest -n auto --dist loadfile

Suites in order, in parallel (smoke, utils, queries, middleware, datadriven):

    python run_suites.py

One or more suites:

    python run_suites.py smoke
    python run_suites.py utils queries

Same, but without parallelism:

    python run_suites.py --serial

By group (markers):

    python -m pytest -m smoke
    python -m pytest -m bva
    python -m pytest -m "ecp and queries"
    python -m pytest -m negative
    python -m pytest -m datadriven

Coverage (optional):

    python -m pytest --cov=tinydb --cov-report=term-missing

## 4. Groups

Two kinds of markers, both registered in pytest.ini (strict markers on, so typos fail).
- By technique: smoke, ecp, bva, negative, datadriven
- By module: utils, queries, middleware

## 5. Execution order

conftest.py reorders the collected tests:
1. Group order: smoke, ecp, bva, negative, datadriven
2. Inside a group, tests with `@pytest.mark.run_order(n)` run by ascending n (see TestCachingFlush)
3. Everything else keeps file and definition order

A serial run gives this exact global order. With xdist each worker follows the same order for the files it owns. run_suites.py adds a second level: suites run one after another, parallel inside each suite.

## 6. Parameterization and data driven tests

- `@pytest.mark.parametrize` is used for boundary values (capacity sizes, age 17/18/19, flush thresholds) and mutation lists.
- test_csv_driven.py reads four CSV files. To add a case, add a row to the CSV. No Python change needed.

## 7. Before you submit

- Each test file names its owner at the top (Huzaifa Imran or Musab Butt). Commit each member's files from their own account so the Git history shows individual work.
- Put the setup video in `automation/setup_video/`.
- Make the repository public, submit the link on GCR, and push nothing after the due date.

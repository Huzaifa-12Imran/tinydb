# TinyDB Unit Test Automation — Assignment 3

## Project Overview

This project focuses on automated unit testing of [TinyDB](https://github.com/msiemens/tinydb), a lightweight, pure-Python database licensed under the MIT License.

The objective is to design and execute unit tests using **pytest**, applying techniques such as Equivalence Class Partitioning (ECP), Boundary Value Analysis (BVA), negative testing, and data-driven testing.

All assignment-related files are organized inside the `automation/` folder. The original `tinydb` package and its existing `tests/` directory remain unchanged.

### Modules Under Test

1. **`tinydb/utils.py`** — `LRUCache`, `freeze`, and `FrozenDict`
2. **`tinydb/queries.py`** — `Query` and `QueryInstance`
3. **`tinydb/middlewares.py`** — `Middleware` and `CachingMiddleware`

---

## Task 1: Environment Setup

### Prerequisites

- Python 3.9 or newer
- Git
- pip

### Step 1: Clone the Repository

Open a terminal and run:

```bash
git clone https://github.com/Huzaifa-12Imran/tinydb.git
cd tinydb
```

### Step 2: Create a Virtual Environment

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Linux or macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies

Run the following commands from the repository root:

```bash
python -m pip install -e .
python -m pip install -r automation/requirements-test.txt
```

### Step 4: Verify the Installation

Check the Python version:

```bash
python --version
```

Navigate to the automation directory:

```bash
cd automation
```

Verify pytest is installed:

```bash
python -m pytest --version
```

Run the test suite:

```bash
python -m pytest -q
```

**Expected result:** All tests should pass. The expected baseline is 239 passing tests, as reported when this assignment was prepared. Actual results may vary if the test suite or dependencies have changed.

### Step 5: Record the Setup

Record a screen video demonstrating the environment setup and test execution. Save the recording in:

```text
automation/setup_video/
```

---

## Project Structure

The assignment files are organized as follows:

```text
automation/
├── pytest.ini
├── conftest.py
├── run_suites.py
├── requirements-test.txt
│
├── unit_tests/
│   ├── test_utils_lrucache.py
│   ├── test_utils_freeze.py
│   ├── test_queries.py
│   ├── test_middlewares.py
│   ├── test_csv_driven.py
│   └── csv_data.py
│
├── data/
│   ├── query_cases.csv
│   ├── lru_cases.csv
│   ├── cache_flush_cases.csv
│   └── freeze_cases.csv
│
├── docs/
│   ├── ECP_BVA_NOTES.md
│   └── TestCases.xlsx
│
└── setup_video/
```

### File Descriptions

| File or Folder | Purpose |
|---|---|
| `pytest.ini` | Configures pytest markers, strict marker validation, and default test discovery. |
| `conftest.py` | Provides shared fixtures, including `CountingMemoryStorage`, and controls test execution order. |
| `run_suites.py` | Executes selected test suites in a predefined sequence. |
| `requirements-test.txt` | Lists the dependencies required for testing. |
| `unit_tests/` | Contains the unit tests for the selected TinyDB modules. |
| `data/` | Contains CSV files used for data-driven testing. |
| `docs/ECP_BVA_NOTES.md` | Documents the test design and ECP/BVA techniques. |
| `docs/TestCases.xlsx` | Contains the test case documentation. |
| `setup_video/` | Stores the environment setup recording. |

---

## Task 2: Test Design Techniques

The test suite applies several software testing techniques to improve test coverage and verify expected behavior.

### 1. Equivalence Class Partitioning (ECP)

Input values are divided into groups expected to behave similarly. Representative values from each group are selected for testing.

### 2. Boundary Value Analysis (BVA)

Tests focus on values at, below, and above important boundaries, such as cache capacities, age limits, and cache flush thresholds.

### 3. Negative Testing

Invalid inputs and unexpected conditions are tested to verify that the system behaves correctly when errors occur.

### 4. Data-Driven Testing

Test cases are loaded from CSV files, allowing new test scenarios to be added by inserting rows without changing the Python test code.

Detailed test design notes are available in `docs/ECP_BVA_NOTES.md`.

---

## Task 3: Test Case Documentation

Test cases are documented in `docs/TestCases.xlsx`.

The test suite also uses CSV files for data-driven testing:

- `query_cases.csv` — Query-related test scenarios
- `lru_cases.csv` — LRU cache test scenarios
- `cache_flush_cases.csv` — Cache flushing scenarios
- `freeze_cases.csv` — `freeze` and immutable data structure scenarios

The CSV loader is implemented in `unit_tests/csv_data.py`, and the tests are executed through `unit_tests/test_csv_driven.py`.

To add a data-driven test case, add a row to the appropriate CSV file while following its existing column structure.

---

## Task 4: Running the Tests

**Important:** Run the following commands from the `automation/` directory with the virtual environment activated.

### 1. Run All Tests Sequentially

```bash
python -m pytest
```

### 2. Run All Tests in Parallel

```bash
python -m pytest -n auto --dist loadfile
```

This command uses `pytest-xdist` to distribute test files among multiple workers.

### 3. Run Test Suites in a Fixed Order

Run all configured suites:

```bash
python run_suites.py
```

Run individual suites:

```bash
python run_suites.py smoke
python run_suites.py utils queries
```

Run the selected suites without parallel execution:

```bash
python run_suites.py --serial
```

The available suite names are:

- `smoke`
- `utils`
- `queries`
- `middleware`
- `datadriven`

### 4. Run Tests by Marker

Tests can also be selected using pytest markers.

Run smoke tests:

```bash
python -m pytest -m smoke
```

Run Boundary Value Analysis tests:

```bash
python -m pytest -m bva
```

Run ECP tests for the query module:

```bash
python -m pytest -m "ecp and queries"
```

Run negative tests:

```bash
python -m pytest -m negative
```

Run data-driven tests:

```bash
python -m pytest -m datadriven
```

### 5. Generate a Coverage Report (Optional)

```bash
python -m pytest --cov=tinydb --cov-report=term-missing
```

This command displays a coverage summary and identifies lines that were not executed by the tests. The required coverage dependencies must be installed.

---

## Test Organization and Execution Order

### Test Markers

The project uses two categories of pytest markers.

**Testing techniques:**

- `smoke`
- `ecp`
- `bva`
- `negative`
- `datadriven`

**Modules under test:**

- `utils`
- `queries`
- `middleware`

Markers are registered in `pytest.ini`, and strict marker validation helps detect misspelled or unregistered markers.

### Execution Order

The `conftest.py` configuration controls test ordering as follows:

1. **Group priority:** Smoke tests, ECP tests, BVA tests, negative tests, and data-driven tests.
2. **Explicit ordering:** Tests decorated with `@pytest.mark.run_order(n)` are ordered by ascending `n` within the applicable group.
3. **Default ordering:** Tests without an explicit order retain their collected file and definition order, subject to the configured ordering hook.

A sequential run applies the configured ordering to the collected tests. With pytest-xdist, ordering applies within each worker's assigned files; parallel execution does not guarantee one exact global order across all workers.

The `run_suites.py` script provides an additional level of organization by running suites sequentially while allowing parallel execution within individual suites when configured.

---

## Parameterization and Data-Driven Testing

The project uses pytest parameterization to test multiple inputs efficiently.

Examples include:

- Different cache capacity values
- Age boundary values such as 17, 18, and 19
- Different cache flush thresholds
- Multiple mutation scenarios

The `@pytest.mark.parametrize` decorator allows the same test logic to run against several input values.

CSV-driven tests provide an additional way to expand test coverage. New scenarios can be introduced by adding rows to the appropriate CSV file, without modifying the original TinyDB source code.

---

## Before Submission

Complete the following checklist before submitting the assignment:

- [ ] Verify that the environment setup works correctly.
- [ ] Run the complete test suite and review the results.
- [ ] Ensure that the test case documentation in `docs/TestCases.xlsx` is complete.
- [ ] Ensure that the ECP/BVA notes are included in `docs/ECP_BVA_NOTES.md`.
- [ ] Save the setup video in `automation/setup_video/`.
- [ ] Confirm that each test file identifies its respective owner at the top.
- [ ] Commit each member's assigned files using that member's own Git account so the commit history reflects individual contributions.
- [ ] Make the repository public.
- [ ] Submit the repository link on GCR before the deadline.
- [ ] Do not push additional changes after the submission deadline.

---

## License

TinyDB is distributed under the MIT License. Refer to the original [TinyDB repository](https://github.com/msiemens/tinydb) for its license and project information.

## Acknowledgment

This assignment uses TinyDB as the project under test and focuses on automated unit testing, test design techniques, parameterization, data-driven testing, and organized test execution using pytest.

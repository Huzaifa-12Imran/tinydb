"""
Cross-platform runner for the test suites.

Usage (from the automation folder):
    python run_suites.py              run every suite in order, in parallel
    python run_suites.py --serial     run every suite in order, one process
    python run_suites.py smoke        run one suite by name
    python run_suites.py utils queries

Suites run in this order: smoke, utils, queries, middleware, datadriven.
Each suite is selected with a pytest marker (see pytest.ini) and executed with
pytest-xdist (-n auto) unless --serial is given.
"""
import subprocess
import sys

SUITES = [
    ("smoke", "smoke"),
    ("utils", "utils and not datadriven"),
    ("queries", "queries and not datadriven"),
    ("middleware", "middleware and not datadriven"),
    ("datadriven", "datadriven"),
]


def run_suite(name, expression, serial):
    command = [sys.executable, "-m", "pytest", "-m", expression, "-q"]
    if not serial:
        command += ["-n", "auto", "--dist", "loadfile"]
    print(f"\n=== suite: {name} ({expression}) ===", flush=True)
    return subprocess.call(command)


def main(argv):
    serial = "--serial" in argv
    requested = [arg for arg in argv if not arg.startswith("--")]
    known = dict(SUITES)

    unknown = [name for name in requested if name not in known]
    if unknown:
        print("Unknown suite(s): " + ", ".join(unknown))
        print("Available: " + ", ".join(name for name, _ in SUITES))
        return 2

    selected = [(n, known[n]) for n, _ in SUITES if not requested or n in requested]

    failed = []
    for name, expression in selected:
        if run_suite(name, expression, serial) != 0:
            failed.append(name)

    print("\n=== summary ===")
    print("failed suites: " + (", ".join(failed) if failed else "none"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

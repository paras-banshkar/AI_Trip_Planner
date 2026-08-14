"""
eval/summarize_test_results.py — Turn raw pytest output into one clean report.

`pytest` (per the pyproject.toml config) already writes:
  - test_results.xml   (JUnit: pass/fail/error/skip counts + per-test timing)
  - coverage.xml        (Cobertura: line coverage %, per-file breakdown)
  - htmlcov/index.html  (browsable HTML coverage report)

This script reads the first two and writes a single markdown summary you can
screenshot, attach to a portfolio, or link from your resume/GitHub README.

Usage:
    pytest                              # generates test_results.xml + coverage.xml
    python eval/summarize_test_results.py

Output:
    eval/test_summary.md
"""
import datetime
import os
import sys
import xml.etree.ElementTree as ET

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JUNIT_PATH = os.path.join(ROOT_DIR, "test_results.xml")
COVERAGE_PATH = os.path.join(ROOT_DIR, "coverage.xml")
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_summary.md")


def parse_junit(path):
    if not os.path.exists(path):
        return None
    tree = ET.parse(path)
    root = tree.getroot()
    # pytest's junitxml wraps everything in a <testsuites><testsuite> pair
    suite = root.find("testsuite") if root.tag == "testsuites" else root

    total = int(suite.get("tests", 0))
    failures = int(suite.get("failures", 0))
    errors = int(suite.get("errors", 0))
    skipped = int(suite.get("skipped", 0))
    passed = total - failures - errors - skipped
    time_seconds = float(suite.get("time", 0))

    cases = []
    for case in suite.findall("testcase"):
        name = f"{case.get('classname', '')}::{case.get('name', '')}"
        status = "PASS"
        if case.find("failure") is not None:
            status = "FAIL"
        elif case.find("error") is not None:
            status = "ERROR"
        elif case.find("skipped") is not None:
            status = "SKIPPED"
        cases.append((name, status, float(case.get("time", 0))))

    return {
        "total": total,
        "passed": passed,
        "failures": failures,
        "errors": errors,
        "skipped": skipped,
        "time_seconds": time_seconds,
        "cases": cases,
    }


def parse_coverage(path):
    if not os.path.exists(path):
        return None
    tree = ET.parse(path)
    root = tree.getroot()
    line_rate = float(root.get("line-rate", 0)) * 100

    per_file = []
    for package in root.findall(".//package"):
        for cls in package.findall(".//class"):
            filename = cls.get("filename", "")
            rate = float(cls.get("line-rate", 0)) * 100
            per_file.append((filename, rate))
    per_file.sort(key=lambda x: x[1])  # worst-covered first

    return {"overall_pct": line_rate, "per_file": per_file}


def render_markdown(junit, coverage):
    lines = []
    lines.append("# Test & Coverage Summary")
    lines.append("")
    lines.append(f"_Generated {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")
    lines.append("")

    if junit:
        pass_rate = (junit["passed"] / junit["total"] * 100) if junit["total"] else 0
        lines.append("## Tests")
        lines.append("")
        lines.append(f"- **{junit['passed']}/{junit['total']} passed** ({pass_rate:.1f}%)")
        if junit["failures"]:
            lines.append(f"- {junit['failures']} failing")
        if junit["errors"]:
            lines.append(f"- {junit['errors']} errored")
        if junit["skipped"]:
            lines.append(f"- {junit['skipped']} skipped")
        lines.append(f"- Total run time: {junit['time_seconds']:.2f}s")
        lines.append("")

        failing = [c for c in junit["cases"] if c[1] != "PASS"]
        if failing:
            lines.append("### Failing / errored tests")
            lines.append("")
            for name, status, _ in failing:
                lines.append(f"- `{name}` — {status}")
            lines.append("")
    else:
        lines.append("## Tests")
        lines.append("")
        lines.append("_No test_results.xml found — run `pytest` first._")
        lines.append("")

    if coverage:
        lines.append("## Coverage")
        lines.append("")
        lines.append(f"- **Overall line coverage: {coverage['overall_pct']:.1f}%**")
        lines.append("")
        lines.append("| File | Coverage |")
        lines.append("|---|---|")
        for filename, rate in coverage["per_file"]:
            lines.append(f"| {filename} | {rate:.1f}% |")
        lines.append("")
    else:
        lines.append("## Coverage")
        lines.append("")
        lines.append("_No coverage.xml found — run `pytest` first._")
        lines.append("")

    return "\n".join(lines)


def main():
    junit = parse_junit(JUNIT_PATH)
    coverage = parse_coverage(COVERAGE_PATH)

    if junit is None and coverage is None:
        print("Nothing to summarize yet. Run `pytest` first (see pyproject.toml addopts).")
        sys.exit(1)

    report = render_markdown(junit, coverage)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(report)

    print(report)
    print(f"\nSaved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
End-to-end tests for the beancount-query skill.

These tests verify the full workflow:
  1. User sends a natural language prompt via `opencode run`
  2. The AI loads the beancount-query skill
  3. The AI constructs and executes a bean-query command
  4. The final response contains correct, formatted data

Each test sends a prompt to `opencode run --format json --dir <ledger_dir>`,
parses the JSON event stream, and asserts on:
  - skill_loaded:  the beancount-query skill was loaded
  - bean_query_ran: bean-query was invoked via bash
  - bql_contains:   the BQL query contains expected keywords (optional)
  - response_contains: the final text response contains expected strings

Requirements:
    - opencode CLI installed and on PATH
    - bean-query installed (pip install beancount or beanquery)
    - The skill symlink exists: <ledger_dir>/.claude/skills/beancount-query

Usage:
    python3 tests/test_e2e.py                                   # use bundled sample.beancount
    python3 tests/test_e2e.py /path/to/ledger-dir               # use a custom ledger directory
    python3 tests/test_e2e.py --test "test_name"                 # run a specific test
    python3 tests/test_e2e.py --list                             # list all test names
    python3 tests/test_e2e.py --timeout 120                      # custom timeout per test (seconds)

NOTE: These tests call a real LLM via opencode and are non-deterministic.
      A test "passes" if the LLM produces a response that meets the assertions.
      Expect occasional flakiness due to LLM variability.
      Each test invocation costs API tokens.
"""

import json
import subprocess
import sys
import shutil
import time
from pathlib import Path
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TESTS_DIR = Path(__file__).resolve().parent
SKILL_DIR = TESTS_DIR.parent
# Default: use the sample ledger — requires a temporary skill symlink setup
DEFAULT_LEDGER_DIR = TESTS_DIR

DEFAULT_TIMEOUT = 180  # seconds per test


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class E2ETest:
    """Definition of a single end-to-end test case."""
    name: str
    prompt: str
    # Assertions on the event stream
    expect_skill_loaded: bool = True
    expect_bean_query: bool = True
    bql_contains: list[str] = field(default_factory=list)
    response_contains: list[str] = field(default_factory=list)
    response_not_contains: list[str] = field(default_factory=list)


@dataclass
class E2EResult:
    """Result of running a single e2e test."""
    name: str
    passed: bool
    duration: float  # seconds
    failure_reason: str = ""
    skill_loaded: bool = False
    bean_query_ran: bool = False
    bql_queries: list[str] = field(default_factory=list)
    response_text: str = ""


# ---------------------------------------------------------------------------
# Test definitions
#
# We test a representative subset of modules to keep cost and time reasonable.
# Each prompt is designed to be unambiguous so the LLM reliably picks the
# correct query template.
# ---------------------------------------------------------------------------

E2E_TESTS = [
    # Module 1: Account Listing
    E2ETest(
        name="account_listing",
        prompt="List all accounts in sample.beancount",
        bql_contains=["account"],
        response_contains=["Assets:Bank:ICBC", "Expenses:Food:Dining", "Income:Salary"],
    ),

    # Module 2: Balance Inquiry
    E2ETest(
        name="balance_inquiry",
        prompt="What is the balance of Assets:Bank:ICBC in sample.beancount?",
        bql_contains=["ICBC"],
        response_contains=["ICBC", "75,505"],
    ),

    # Module 3: Net Worth
    E2ETest(
        name="net_worth",
        prompt="What is my net worth based on sample.beancount?",
        bql_contains=["Assets", "Liabilities"],
        response_contains=["371,288"],
    ),

    # Module 4: Expense Analysis
    E2ETest(
        name="expense_analysis",
        prompt="Show my expenses by category for Q1 2024 from sample.beancount",
        bql_contains=["Expenses"],
        response_contains=["Rent", "7,000", "9,894"],
    ),

    # Module 5: Income Analysis
    E2ETest(
        name="income_analysis",
        prompt="How much income did I receive in the first half of 2024? Use sample.beancount",
        bql_contains=["Income"],
        response_contains=["Salary", "60,000"],
    ),

    # Module 6: Trend Analysis
    E2ETest(
        name="monthly_trend",
        prompt="Show monthly expense trend for 2024 from sample.beancount",
        bql_contains=["month"],
        response_contains=["4,015", "1,879"],
    ),

    # Module 8: Transaction Journal
    E2ETest(
        name="search_transactions",
        prompt="Find all transactions mentioning 'Salary' in sample.beancount",
        bql_contains=["Salary"],
        response_contains=["Salary", "15,000"],
    ),

    # Module 9: Liability Overview
    E2ETest(
        name="liabilities",
        prompt="Show all my liabilities from sample.beancount",
        bql_contains=["Liabilities"],
        response_contains=["Mortgage", "480,000"],
    ),
]


# ---------------------------------------------------------------------------
# Event stream parser
# ---------------------------------------------------------------------------

def parse_opencode_events(raw_output: str) -> dict:
    """
    Parse the JSON event stream from `opencode run --format json`.

    The event stream consists of newline-delimited JSON objects with the format:
        {"type": "...", "timestamp": ..., "sessionID": "...", "part": {...}}

    Event types:
        - step_start / step_finish: step boundaries
        - tool_use: a tool call; part.tool is the tool name, part.state has input/output
        - text: AI response text; part.text has the content

    Returns a dict with:
        skill_loaded: bool — whether the beancount-query skill was loaded
        bean_query_ran: bool — whether bean-query was called via bash
        bql_queries: list[str] — BQL queries extracted from bash commands
        response_text: str — the final text response from the AI
        tool_uses: list[dict] — all tool_use events for debugging
    """
    result = {
        "skill_loaded": False,
        "bean_query_ran": False,
        "bql_queries": [],
        "response_text": "",
        "tool_uses": [],
    }

    for line in raw_output.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        event_type = event.get("type", "")
        part = event.get("part", {})

        if event_type == "tool_use":
            result["tool_uses"].append(event)

            # Tool name is in part.tool
            tool_name = part.get("tool", "")
            # Input/output are in part.state
            state = part.get("state", {})
            tool_input = state.get("input", {})

            # Check for skill loading
            if tool_name == "skill":
                input_str = json.dumps(tool_input) if isinstance(tool_input, dict) else str(tool_input)
                if "beancount-query" in input_str or "beancount_query" in input_str:
                    result["skill_loaded"] = True

            # Check for bean-query execution via bash
            if tool_name == "bash":
                cmd = ""
                if isinstance(tool_input, dict):
                    cmd = tool_input.get("command", "")
                elif isinstance(tool_input, str):
                    cmd = tool_input

                if "bean-query" in cmd:
                    result["bean_query_ran"] = True
                    result["bql_queries"].append(cmd)

        elif event_type == "text":
            # Response text is in part.text
            content = part.get("text", "")
            result["response_text"] += content

    return result


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

def run_e2e_test(test: E2ETest, ledger_dir: Path, timeout: int) -> E2EResult:
    """Run a single e2e test and return the result."""
    result = E2EResult(name=test.name, passed=False, duration=0.0)

    start = time.time()
    try:
        proc = subprocess.run(
            ["opencode", "run", "--format", "json", "--dir", str(ledger_dir), test.prompt],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        result.duration = time.time() - start

        if proc.returncode != 0:
            result.failure_reason = f"opencode exited with code {proc.returncode}: {proc.stderr[:200]}"
            return result

        raw = proc.stdout
        if not raw.strip():
            result.failure_reason = "opencode produced no output"
            return result

        parsed = parse_opencode_events(raw)
        result.skill_loaded = parsed["skill_loaded"]
        result.bean_query_ran = parsed["bean_query_ran"]
        result.bql_queries = parsed["bql_queries"]
        result.response_text = parsed["response_text"]

    except subprocess.TimeoutExpired:
        result.duration = time.time() - start
        result.failure_reason = f"Timed out after {timeout}s"
        return result
    except Exception as e:
        result.duration = time.time() - start
        result.failure_reason = f"Exception: {e}"
        return result

    # --- Assertions ---
    failures = []

    # 1. Skill loaded
    if test.expect_skill_loaded and not result.skill_loaded:
        failures.append("beancount-query skill was NOT loaded")

    # 2. bean-query ran
    if test.expect_bean_query and not result.bean_query_ran:
        failures.append("bean-query was NOT executed")

    # 3. BQL query contains expected keywords
    all_bql = " ".join(result.bql_queries).lower()
    for keyword in test.bql_contains:
        if keyword.lower() not in all_bql:
            failures.append(f"BQL missing keyword: '{keyword}'")

    # 4. Response contains expected strings
    response_lower = result.response_text.lower()
    for expected in test.response_contains:
        if expected.lower() not in response_lower:
            failures.append(f"Response missing: '{expected}'")

    # 5. Response does NOT contain certain strings
    for forbidden in test.response_not_contains:
        if forbidden.lower() in response_lower:
            failures.append(f"Response unexpectedly contains: '{forbidden}'")

    if failures:
        result.failure_reason = "; ".join(failures)
    else:
        result.passed = True

    return result


def setup_skill_symlink(ledger_dir: Path) -> bool:
    """Ensure the skill symlink exists in the ledger directory."""
    skills_dir = ledger_dir / ".claude" / "skills"
    symlink_path = skills_dir / "beancount-query"
    skill_source = SKILL_DIR / "beancount-query"

    if symlink_path.exists() or symlink_path.is_symlink():
        return True

    try:
        skills_dir.mkdir(parents=True, exist_ok=True)
        symlink_path.symlink_to(skill_source)
        print(f"  Created symlink: {symlink_path} -> {skill_source}")
        return True
    except Exception as e:
        print(f"  WARNING: Could not create skill symlink: {e}")
        return False


def main():
    import argparse

    parser = argparse.ArgumentParser(description="End-to-end tests for beancount-query skill")
    parser.add_argument("ledger_dir", nargs="?", default=None,
                        help="Directory containing .beancount file(s) and .claude/skills symlink")
    parser.add_argument("--test", "-t", default=None,
                        help="Run only the named test")
    parser.add_argument("--list", "-l", action="store_true",
                        help="List all test names and exit")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                        help=f"Timeout per test in seconds (default: {DEFAULT_TIMEOUT})")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show detailed output including response text")
    args = parser.parse_args()

    if args.list:
        for t in E2E_TESTS:
            print(f"  {t.name}")
        return

    # Check opencode is available
    if not shutil.which("opencode"):
        print("FATAL: 'opencode' CLI not found on PATH")
        sys.exit(2)

    # Determine ledger directory
    if args.ledger_dir:
        ledger_dir = Path(args.ledger_dir).resolve()
    else:
        # Default: use the tests/ directory which contains sample.beancount
        ledger_dir = TESTS_DIR

    if not ledger_dir.is_dir():
        print(f"FATAL: Not a directory: {ledger_dir}")
        sys.exit(2)

    # Ensure skill symlink exists
    setup_skill_symlink(ledger_dir)

    # Select tests to run
    tests = E2E_TESTS
    if args.test:
        tests = [t for t in E2E_TESTS if t.name == args.test]
        if not tests:
            print(f"FATAL: No test named '{args.test}'. Use --list to see available tests.")
            sys.exit(2)

    print(f"Ledger dir:   {ledger_dir}")
    print(f"Tests:        {len(tests)}")
    print(f"Timeout:      {args.timeout}s per test")
    print(f"NOTE: These tests invoke a real LLM and cost API tokens.")
    print("-" * 70)

    passed = 0
    failed = 0
    results: list[E2EResult] = []

    for test in tests:
        print(f"\n  Running: {test.name} ...")
        print(f"  Prompt:  \"{test.prompt}\"")

        result = run_e2e_test(test, ledger_dir, args.timeout)
        results.append(result)

        status = "PASS" if result.passed else "FAIL"
        print(f"  {status}     {test.name}  ({result.duration:.1f}s)")
        if result.skill_loaded:
            print(f"           skill loaded: yes")
        if result.bean_query_ran:
            print(f"           bean-query ran: yes ({len(result.bql_queries)} call(s))")
        if not result.passed:
            print(f"           reason: {result.failure_reason}")

        if args.verbose and result.response_text:
            print(f"\n  --- Response (first 500 chars) ---")
            print(f"  {result.response_text[:500]}")
            print(f"  --- End ---\n")

        if result.passed:
            passed += 1
        else:
            failed += 1

    # Summary
    print("\n" + "=" * 70)
    total = passed + failed
    total_time = sum(r.duration for r in results)
    print(f"Result: {passed}/{total} passed, {failed} failed  ({total_time:.1f}s total)")

    if failed > 0:
        print(f"\nFAILED TESTS:")
        for r in results:
            if not r.passed:
                print(f"  [{r.name}] {r.failure_reason}")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Test suite for beancount-query skill.

Validates that all query templates from query-patterns.md execute successfully
against the sample beancount file. Each test verifies:
  1. bean-query exits with code 0 (no syntax/runtime errors)
  2. stdout is non-empty (query produces output)
  3. Row count matches expected (when using the bundled sample ledger)
  4. Output contains expected key strings (when using the bundled sample ledger)

Usage:
    python3 tests/test_queries.py                          # use bundled sample.beancount
    python3 tests/test_queries.py /path/to/your.beancount  # use a custom ledger file

When a custom ledger is provided, only checks 1 & 2 are enforced (syntax + non-empty).
Checks 3 & 4 (row count + content) are only enforced against the bundled sample file,
because expected values are derived from its fixed data.

Requirements:
    - bean-query (pip install beancount or beanquery)
"""

import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TESTS_DIR = Path(__file__).resolve().parent
DEFAULT_LEDGER = TESTS_DIR / "sample.beancount"

# ---------------------------------------------------------------------------
# Test definitions
#
# Each entry is a dict:
#   name:     str  — test identifier
#   query:    str  — BQL query string
#   rows:     int  — expected data row count (excluding header/separator)
#   contains: list — strings that must appear in stdout
#
# `rows` and `contains` are only checked against the bundled sample ledger.
# Organized by the 12 modules in query-patterns.md
# ---------------------------------------------------------------------------

QUERY_TESTS = [
    # ── Module 1: Account Listing ──
    {
        "name": "1.1 all_accounts",
        "query": "SELECT DISTINCT account ORDER BY account",
        "rows": 19,
        "contains": ["Assets:Bank:ICBC", "Expenses:Food:Dining", "Income:Salary",
                      "Liabilities:Mortgage", "Equity:Budget:Travel"],
    },
    {
        "name": "1.2 accounts_by_type",
        "query": "SELECT DISTINCT account WHERE account ~ 'Assets' ORDER BY account",
        "rows": 4,
        "contains": ["Assets:Alipay", "Assets:Bank:CMB", "Assets:Bank:ICBC", "Assets:Cash"],
    },
    {
        "name": "1.3 accounts_with_open_date",
        "query": "SELECT account, open_date(account) AS opened FROM accounts ORDER BY account",
        "rows": None,  # FROM accounts returns all postings, count varies
        "contains": ["1970-01-01"],
    },

    # ── Module 2: Balance Inquiry ──
    {
        "name": "2.1 all_balances",
        "query": "BALANCES",
        "rows": None,
        "contains": ["Assets:Bank:ICBC", "Liabilities:Mortgage"],
    },
    {
        "name": "2.2 balances_by_type",
        "query": "SELECT account, sum(position) AS balance WHERE account ~ 'Assets' GROUP BY account ORDER BY account",
        "rows": 4,
        "contains": ["Assets:Bank:ICBC", "CNY"],
    },
    {
        "name": "2.3 balance_specific_account",
        "query": "SELECT account, sum(position) AS balance WHERE account ~ 'Bank:ICBC' GROUP BY account",
        "rows": 1,
        "contains": ["Assets:Bank:ICBC", "CNY"],
    },
    {
        "name": "2.4 balances_at_date",
        "query": "SELECT account, sum(position) AS balance FROM date <= 2024-03-31 WHERE account ~ 'Assets' GROUP BY account ORDER BY account",
        "rows": 4,
        "contains": ["Assets:Alipay", "Assets:Cash"],
    },

    # ── Module 3: Net Worth ──
    {
        "name": "3.1 net_worth",
        "query": "SELECT sum(position) AS net_worth WHERE account ~ 'Assets|Liabilities'",
        "rows": 1,
        "contains": ["-371288.50 CNY"],
    },
    {
        "name": "3.2 net_worth_breakdown",
        "query": "SELECT root(account, 1) AS type, sum(position) AS total WHERE account ~ 'Assets|Liabilities' GROUP BY root(account, 1)",
        "rows": 2,
        "contains": ["Assets", "Liabilities"],
    },
    {
        "name": "3.3 net_worth_at_date",
        "query": "SELECT sum(position) AS net_worth FROM date <= 2024-03-31 WHERE account ~ 'Assets|Liabilities'",
        "rows": 1,
        "contains": ["CNY"],
    },

    # ── Module 4: Expense Analysis ──
    {
        "name": "4.1 total_expenses_period",
        "query": "SELECT sum(number) AS total WHERE account ~ 'Expenses' AND date >= 2024-01-01 AND date < 2024-04-01",
        "rows": 1,
        "contains": ["9894.00"],
    },
    {
        "name": "4.2 expenses_by_category",
        "query": "SELECT account, sum(number) AS total WHERE account ~ 'Expenses' AND date >= 2024-01-01 AND date < 2024-04-01 GROUP BY account ORDER BY total DESC",
        "rows": 7,
        "contains": ["Expenses:Housing:Rent", "Expenses:Food:Dining", "Expenses:Education"],
    },
    {
        "name": "4.3 expenses_by_subcategory",
        "query": "SELECT leaf(account) AS category, sum(number) AS total WHERE account ~ 'Expenses:Food' AND date >= 2024-01-01 AND date < 2024-07-01 GROUP BY leaf(account) ORDER BY total DESC",
        "rows": 2,
        "contains": ["Dining", "Groceries"],
    },
    {
        "name": "4.4 expenses_this_month_pattern",
        "query": "SELECT account, sum(number) AS total WHERE account ~ 'Expenses' AND year = 2024 AND month = 1 GROUP BY account ORDER BY total DESC",
        "rows": 4,
        "contains": ["Expenses:Housing:Rent", "3500.00"],
    },
    {
        "name": "4.5 specific_category_detail",
        "query": "SELECT date, narration, number, currency WHERE account ~ 'Expenses:Food' AND date >= 2024-01-01 AND date < 2024-04-01 ORDER BY date",
        "rows": 4,
        "contains": ["Dining out", "Groceries", "120.00", "350.00"],
    },

    # ── Module 5: Income Analysis ──
    {
        "name": "5.1 total_income_period",
        "query": "SELECT sum(number) AS total WHERE account ~ 'Income' AND date >= 2024-01-01 AND date < 2024-04-01",
        "rows": 1,
        "contains": ["-48000.00"],
    },
    {
        "name": "5.2 income_by_source",
        "query": "SELECT account, neg(sum(number)) AS total WHERE account ~ 'Income' AND date >= 2024-01-01 AND date < 2024-07-01 GROUP BY account ORDER BY total DESC",
        "rows": 3,
        "contains": ["Income:Salary", "60000.00", "Income:Freelance", "3000.00",
                      "Income:Interest", "85.50"],
    },
    {
        "name": "5.3 annual_income",
        "query": "SELECT year, neg(sum(number)) AS total WHERE account ~ 'Income' GROUP BY year ORDER BY year",
        "rows": 1,
        "contains": ["2024", "63085.50"],
    },

    # ── Module 6: Trend Analysis ──
    {
        "name": "6.1 monthly_expense_trend",
        "query": "SELECT year, month, sum(number) AS total WHERE account ~ 'Expenses' AND date >= 2024-01-01 GROUP BY year, month ORDER BY year, month",
        "rows": 4,
        "contains": ["2024", "4015.00", "1879.00", "4000.00", "3980.00"],
    },
    {
        "name": "6.2 monthly_expense_specific_year",
        "query": "SELECT month, sum(number) AS total WHERE account ~ 'Expenses' AND year = 2024 GROUP BY month ORDER BY month",
        "rows": 4,
        "contains": ["4015.00", "1879.00", "4000.00", "3980.00"],
    },
    {
        "name": "6.3 yearly_expense_comparison",
        "query": "SELECT year, sum(number) AS expenses WHERE account ~ 'Expenses' GROUP BY year ORDER BY year",
        "rows": 1,
        "contains": ["2024", "13874.00"],
    },
    {
        "name": "6.4 monthly_trend_category",
        "query": "SELECT year, month, sum(number) AS total WHERE account ~ 'Expenses:Food' AND date >= 2024-01-01 GROUP BY year, month ORDER BY year, month",
        "rows": 4,
        "contains": ["470.00", "580.00", "420.00", "200.00"],
    },
    {
        "name": "6.5 quarterly_summary",
        "query": "SELECT year, quarter(date) AS quarter, sum(number) AS total WHERE account ~ 'Expenses' AND year = 2024 GROUP BY year, quarter(date) ORDER BY year, quarter(date)",
        "rows": 2,
        "contains": ["9894.00", "3980.00"],
    },

    # ── Module 7: Category Ranking ──
    {
        "name": "7.1 top_expense_categories",
        "query": "SELECT account, sum(number) AS total WHERE account ~ 'Expenses' GROUP BY account ORDER BY total DESC LIMIT 5",
        "rows": 5,
        "contains": ["Expenses:Housing:Rent", "10500.00"],
    },
    {
        "name": "7.2 top_expenses_period",
        "query": "SELECT account, sum(number) AS total WHERE account ~ 'Expenses' AND date >= 2024-01-01 AND date < 2024-04-01 GROUP BY account ORDER BY total DESC LIMIT 5",
        "rows": 5,
        "contains": ["Expenses:Housing:Rent", "7000.00"],
    },
    {
        "name": "7.3 largest_single_transactions",
        "query": "SELECT date, narration, account, number, currency WHERE account ~ 'Expenses' ORDER BY number DESC LIMIT 5",
        "rows": 5,
        "contains": ["Rent", "3500.00"],
    },
    {
        "name": "7.4 most_frequent_categories",
        "query": "SELECT account, count(*) AS frequency WHERE account ~ 'Expenses' GROUP BY account ORDER BY frequency DESC LIMIT 5",
        "rows": 5,
        "contains": ["Expenses:Housing:Rent"],
    },
    {
        "name": "7.5 top_by_leaf_name",
        "query": "SELECT leaf(account) AS category, sum(number) AS total WHERE account ~ 'Expenses' GROUP BY leaf(account) ORDER BY total DESC LIMIT 5",
        "rows": 5,
        "contains": ["Rent", "10500.00"],
    },

    # ── Module 8: Transaction Journal ──
    {
        "name": "8.1 recent_transactions",
        "query": "SELECT date, narration, account, number, currency ORDER BY date DESC LIMIT 10",
        "rows": 10,
        "contains": ["Credit card repayment", "Budget allocation"],
    },
    {
        "name": "8.2 journal_specific_account",
        "query": "JOURNAL 'Assets:Bank:ICBC' FROM date >= 2024-01-01",
        "rows": None,  # JOURNAL output format differs
        "contains": ["Assets:Bank:ICBC"],
    },
    {
        "name": "8.3 transactions_date_range",
        "query": "SELECT date, narration, number, currency, other_accounts WHERE account ~ 'Assets:Bank:ICBC' AND date >= 2024-01-01 AND date < 2024-04-01 ORDER BY date",
        "rows": 9,
        "contains": ["Salary", "Rent", "Mortgage"],
    },
    {
        "name": "8.4 search_by_narration",
        "query": "SELECT date, narration, account, number, currency WHERE narration ~ 'Salary' ORDER BY date DESC",
        "rows": 8,
        "contains": ["Salary", "Income:Salary", "15000.00"],
    },

    # ── Module 9: Liability Overview ──
    {
        "name": "9.1 all_liabilities",
        "query": "SELECT account, sum(position) AS balance WHERE account ~ 'Liabilities' GROUP BY account ORDER BY account",
        "rows": 2,
        "contains": ["Liabilities:CreditCard:ICBC", "Liabilities:Mortgage", "-480000.00"],
    },
    {
        "name": "9.2 specific_liability",
        "query": "SELECT account, sum(position) AS balance WHERE account ~ 'Mortgage' GROUP BY account",
        "rows": 1,
        "contains": ["Liabilities:Mortgage", "-480000.00 CNY"],
    },
    {
        "name": "9.3 liability_payments",
        "query": "SELECT date, narration, number, currency WHERE account ~ 'Mortgage' AND number > 0 ORDER BY date DESC LIMIT 5",
        "rows": 4,
        "contains": ["Mortgage payment", "5000.00"],
    },
    {
        "name": "9.4 total_debt",
        "query": "SELECT neg(sum(position)) AS total_debt WHERE account ~ 'Liabilities'",
        "rows": 1,
        "contains": ["480000.00 CNY"],
    },

    # ── Module 10: Budget Inquiry ──
    {
        "name": "10.1 budget_allocations",
        "query": "SELECT account, sum(position) AS allocated WHERE account ~ 'Equity:Budget' GROUP BY account ORDER BY account",
        "rows": 2,
        "contains": ["Equity:Budget:Electronics", "1500.00",
                      "Equity:Budget:Travel", "2000.00"],
    },
    {
        "name": "10.2 specific_budget",
        "query": "SELECT account, sum(position) AS allocated WHERE account ~ 'Equity:Budget:Travel' GROUP BY account",
        "rows": 1,
        "contains": ["Equity:Budget:Travel", "2000.00 CNY"],
    },

    # ── Module 11: Custom BQL (representative) ──
    {
        "name": "11.1 custom_select_star",
        "query": "SELECT date, account, number, currency LIMIT 3",
        "rows": 3,
        "contains": ["CNY"],
    },

    # ── Module 12: Data Export (query part only, no -f csv flag) ──
    {
        "name": "12.1 export_all_transactions",
        "query": "SELECT date, flag, narration, account, number, currency ORDER BY date LIMIT 10",
        "rows": 10,
        "contains": ["opening balance"],
    },
    {
        "name": "12.2 export_expense_summary",
        "query": "SELECT account, sum(number) AS total WHERE account ~ 'Expenses' GROUP BY account ORDER BY total DESC",
        "rows": 7,
        "contains": ["Expenses:Housing:Rent", "10500.00"],
    },
    {
        "name": "12.3 export_monthly_totals",
        "query": "SELECT year, month, sum(number) AS total WHERE account ~ 'Expenses' GROUP BY year, month ORDER BY year, month",
        "rows": 4,
        "contains": ["2024"],
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run_query(ledger_file: Path, query: str) -> tuple[int, str, str]:
    """Execute a bean-query and return (returncode, stdout, stderr)."""
    result = subprocess.run(
        ["bean-query", "-q", str(ledger_file), query],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.returncode, result.stdout, result.stderr


def count_data_rows(stdout: str) -> int:
    """Count data rows in bean-query text output (exclude header and separator lines)."""
    lines = stdout.strip().split("\n")
    data_lines = [l for l in lines if l.strip() and not set(l.strip()).issubset({"-", " "})]
    return max(0, len(data_lines) - 1)  # subtract the header row


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

def main():
    # Determine ledger file
    if len(sys.argv) > 1:
        ledger = Path(sys.argv[1]).resolve()
    else:
        ledger = DEFAULT_LEDGER

    if not ledger.exists():
        print(f"FATAL: Ledger file not found: {ledger}")
        sys.exit(2)

    use_sample = (ledger == DEFAULT_LEDGER)

    print(f"Ledger:       {ledger}")
    print(f"Tests:        {len(QUERY_TESTS)}")
    print(f"Strict mode:  {'yes (sample ledger — checking rows + content)' if use_sample else 'no (custom ledger — syntax + non-empty only)'}")
    print("-" * 70)

    passed = 0
    failed = 0
    errors = []

    for test in QUERY_TESTS:
        name = test["name"]
        query = test["query"]
        expected_rows = test.get("rows")
        expected_contains = test.get("contains", [])

        try:
            rc, stdout, stderr = run_query(ledger, query)
        except subprocess.TimeoutExpired:
            failed += 1
            errors.append((name, "TIMEOUT", query))
            print(f"  TIMEOUT  {name}")
            continue

        # --- Check 1: exit code ---
        if rc != 0:
            failed += 1
            err_msg = stderr.strip().split("\n")[-1] if stderr.strip() else "unknown error"
            errors.append((name, f"exit={rc}: {err_msg}", query))
            print(f"  FAIL     {name}  [exit code {rc}]")
            continue

        # --- Check 2: non-empty output ---
        if not stdout.strip():
            failed += 1
            errors.append((name, "empty output", query))
            print(f"  FAIL     {name}  [empty output]")
            continue

        actual_rows = count_data_rows(stdout)

        # --- Checks 3 & 4: only against sample ledger ---
        if use_sample:
            # Check 3: row count
            if expected_rows is not None and actual_rows != expected_rows:
                failed += 1
                errors.append((name, f"expected {expected_rows} rows, got {actual_rows}", query))
                print(f"  FAIL     {name}  [expected {expected_rows} rows, got {actual_rows}]")
                continue

            # Check 4: expected content strings
            missing = [s for s in expected_contains if s not in stdout]
            if missing:
                failed += 1
                errors.append((name, f"missing in output: {missing}", query))
                print(f"  FAIL     {name}  [missing: {missing}]")
                continue

        passed += 1
        detail = f"{actual_rows} rows"
        if use_sample and expected_rows is not None:
            detail += ", content ok"
        print(f"  PASS     {name}  ({detail})")

    # Summary
    print("-" * 70)
    total = passed + failed
    print(f"Result: {passed}/{total} passed, {failed} failed")

    if errors:
        print(f"\n{'='*70}")
        print("FAILED TESTS:")
        print(f"{'='*70}")
        for name, reason, query in errors:
            print(f"\n  [{name}]")
            print(f"  Reason: {reason}")
            print(f"  Query:  {query}")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()

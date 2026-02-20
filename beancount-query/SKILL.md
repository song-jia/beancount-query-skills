---
name: beancount-query
description: >-
  Query and analyze beancount ledger data using bean-query. Use this skill when
  the user asks about account balances, expenses, income, net worth, transaction
  history, liabilities, budgets, spending trends, category breakdowns, or needs
  to run BQL queries or export ledger data. Triggers on finance-related
  questions and keywords including: accounts, balance, net worth, expenses,
  income, transactions, journal, budget, trend, export, debt, mortgage, credit
  card, as well as Chinese equivalents such as: 账户, 余额, 净资产, 支出, 花了多少,
  收入, 流水, 交易, 预算, 趋势, 导出, 负债, 房贷, 信用卡.
---

# Beancount Query

Query beancount ledger files via `bean-query` and return structured Markdown results.

## Locating the Ledger File

Determine the beancount file path in this priority order:

1. **User-specified path** — if the user provides an explicit file path, use it directly.
2. **Working directory** — glob for `*.beancount` files in the current working directory. If exactly one file is found, use it. If multiple are found, ask the user to choose.
3. **Prompt the user** — if no `.beancount` file is found, ask the user for the file path.

Cache the resolved path for the session. Verify the file exists before every query execution.

## Core Workflow

For each user query, follow these steps:

1. **Identify intent** — read [references/query-patterns.md](references/query-patterns.md) to match the user's question to a query module (1-12). Infer date ranges, account patterns, and limits from context. Use today's date for relative terms like "this month", "this year", "last quarter".

2. **Construct the BQL query** — select the appropriate template from query-patterns.md and substitute parameters. For ambiguous requests, prefer broader queries and let the user refine.

3. **Execute** — run the query:
   ```bash
   bean-query -q <ledger_file> "<bql_query>"
   ```
   Always use `-q` to suppress validation error output. For CSV export, add `-f csv -o <output_file>`.

4. **Format output** — parse the raw text output and present as described in [Output Formatting](#output-formatting) below.

5. **Interpret** — add a brief natural-language summary after the table explaining key takeaways (e.g., "Your largest expense category this month is dining at 2,345.00 CNY").

## Output Formatting

- Format monetary amounts with **2 decimal places** and currency suffix (e.g., `1,234.56 CNY`).
- For **income** amounts: negate the values so they display as positive numbers (income is stored as negative in beancount).
- For **liability** amounts: show as positive debt amounts (negate the negative balances).

### When to use a Markdown table

Use a Markdown table whenever `bean-query` returns **rows with named columns** — even if there is only one row. The table must include a header row and all result columns.

Examples that **require a table**:
- Account balances (one row per account, columns: account + amount)
- Expense breakdown (one row per category)
- Transaction list (one row per transaction)
- A single account's balance — still a table with one data row

The **only** exception where a table is not needed: a pure scalar result that has no associated label, such as a computed total that the user explicitly asked for as a single number (e.g., "what is my total net worth?"). In that case, present the number inline in bold, then add a supporting table for the breakdown (assets vs. liabilities).

- For result sets **> 20 rows**: show the top entries, then a summary row with totals. Mention the full count.

## Safety Constraints

- **Read-only**: never modify, create, or delete `.beancount` files.
- **Only execute `bean-query`**: do not run other shell commands on the ledger file.
- **Validate user BQL**: for custom queries (module 11), verify the query starts with a valid keyword (`SELECT`, `BALANCES`, `JOURNAL`, `PRINT`) before execution.

## Reference Files

- **[references/query-patterns.md](references/query-patterns.md)** — query templates organized by 12 functional modules. Load this for most queries to find the right template.
- **[references/bql-reference.md](references/bql-reference.md)** — BQL syntax, tables, columns, and functions. Load this only when constructing complex custom queries or when the user asks about BQL capabilities.

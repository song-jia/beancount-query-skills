# beancount-query

An [Agent Skills](https://agentskills.io)-compatible skill that lets you query your [beancount](https://beancount.github.io/) ledger in plain English (or Chinese). Ask questions like "what did I spend on food last month?" and get back a formatted Markdown table with a brief summary — no BQL knowledge required.

## What it does

- Translates natural language questions into BQL (Beancount Query Language) queries
- Executes queries via `bean-query` against your ledger file
- Returns results as Markdown tables with monetary amounts formatted to 2 decimal places
- Adds a brief plain-language summary after each result
- Supports both **English** and **Chinese** questions
- Covers 12 query categories: account listing, balances, net worth, expenses, income, trends, rankings, transaction search, liabilities, budgets, custom BQL, and CSV export

## Requirements

- An AI coding agent that supports the [Agent Skills](https://agentskills.io) open standard (e.g. OpenCode, Claude Code, Cursor, VS Code, Gemini CLI, and [more](https://agentskills.io))
- [beancount](https://beancount.github.io/) / [beanquery](https://github.com/beancount/beanquery) — `bean-query` must be on your PATH

## Installation

Clone this repo and symlink the skill into your ledger's `.claude/skills/` directory:

```bash
git clone https://github.com/YOUR_USERNAME/beancount-query-skill.git
mkdir -p /path/to/your/ledger/.claude/skills
ln -s "$(pwd)/beancount-query-skill/beancount-query" /path/to/your/ledger/.claude/skills/beancount-query
```

Then open your agent from your ledger directory. The skill is picked up automatically — no configuration needed.

> `.claude/skills/` is the standard path recognized by all [Agent Skills](https://agentskills.io)-compatible tools.

## Usage

Just ask questions naturally. Your agent will load the skill, construct and run the appropriate BQL query, and return formatted results.

### Account balances

```
What is the balance of Assets:Bank:ICBC?
```
```
| Account | Balance |
|---------|---------|
| Assets:Bank:ICBC | 75,505.50 CNY |
```

---

```
Show all my asset account balances
```
```
| Account | Balance |
|---------|---------|
| Assets:Alipay | 1,200.00 CNY |
| Assets:Bank:CMB | 32,006.00 CNY |
| Assets:Bank:ICBC | 75,505.50 CNY |
| Assets:Cash | 500.00 CNY |

Total assets: 109,211.50 CNY
```

---

### Expense analysis

```
Show my expenses by category for Q1 2024
```
```
| Category | Total |
|----------|-------|
| Expenses:Housing:Rent | 7,000.00 CNY |
| Expenses:Education | 999.00 CNY |
| Expenses:Food:Groceries | 770.00 CNY |
| Expenses:Food:Dining | 700.00 CNY |
| Expenses:Transport:Gas | 300.00 CNY |
| Expenses:Entertainment | 80.00 CNY |
| Expenses:Transport:Taxi | 45.00 CNY |

Q1 2024 total: 9,894.00 CNY. Housing (rent) is your largest expense at 70.7%.
```

---

### Income

```
How much income did I receive in the first half of 2024?
```
```
| Account | Total |
|---------|-------|
| Income:Salary | 60,000.00 CNY |
| Income:Freelance | 3,000.00 CNY |
| Income:Interest | 85.50 CNY |

H1 2024 total income: 63,085.50 CNY. Salary is your primary source at 95.1%.
```

---

### Net worth

```
What is my net worth?
```
```
Net worth: **-371,288.50 CNY**

| Type | Total |
|------|-------|
| Assets | 108,711.50 CNY |
| Liabilities | -480,000.00 CNY |

Your liabilities (480,000 CNY mortgage) exceed your current assets.
```

---

### Monthly trends

```
Show monthly expense trend for 2024
```
```
| Month | Total |
|-------|-------|
| 1 | 4,015.00 CNY |
| 2 | 1,879.00 CNY |
| 3 | 4,000.00 CNY |
| 4 | 3,980.00 CNY |

February had the lowest spending. Jan, Mar, and Apr are consistently around 4,000 CNY.
```

---

### Transaction search

```
Find all transactions mentioning 'salary'
```
```
| Date | Narration | Account | Amount |
|------|-----------|---------|--------|
| 2024-04-05 | April salary | Assets:Bank:ICBC | 15,000.00 CNY |
| 2024-03-05 | March salary | Assets:Bank:ICBC | 15,000.00 CNY |
| 2024-02-05 | February salary | Assets:Bank:ICBC | 15,000.00 CNY |
| 2024-01-05 | January salary | Assets:Bank:ICBC | 15,000.00 CNY |
```

---

### Chinese queries

The skill supports Chinese-language questions:

```
我上个月花了多少钱？
我的净资产是多少？
列出所有账户
信用卡还欠多少钱？
```

---

### Custom BQL

```
Run this query: SELECT account, sum(number) AS total WHERE account ~ 'Expenses' GROUP BY account ORDER BY total DESC LIMIT 5
```

---

### CSV export

```
Export all my 2024 expenses to expenses_2024.csv
```

## Query categories

| # | Category | Example questions |
|---|----------|-------------------|
| 1 | Account Listing | "list all accounts", "what asset accounts do I have?" |
| 2 | Balance Inquiry | "balance of Assets:Bank:ICBC", "how much is in my savings?" |
| 3 | Net Worth | "what is my net worth?", "total assets and liabilities" |
| 4 | Expense Analysis | "expenses by category last month", "how much did I spend on food?" |
| 5 | Income Analysis | "income this year", "salary received in Q1" |
| 6 | Trend Analysis | "monthly spending trend", "year over year expenses" |
| 7 | Category Ranking | "top 5 expense categories", "where do I spend the most?" |
| 8 | Transaction Journal | "recent transactions", "find all rent payments" |
| 9 | Liability Overview | "show all debts", "mortgage balance", "credit card balance" |
| 10 | Budget Inquiry | "budget allocations", "how much is in my travel budget?" |
| 11 | Custom BQL | "run this query: SELECT ..." |
| 12 | Data Export | "export expenses to CSV" |

## Ledger file resolution

The skill locates your ledger file automatically:

1. If you specify a file path in your question, that is used directly
2. Otherwise it globs for `*.beancount` in the current working directory
3. If multiple files are found, it asks you to choose

## Safety

- **Read-only** — never modifies, creates, or deletes any `.beancount` file
- Only runs `bean-query`; no other shell commands are executed on your ledger

## Running the tests

A self-contained test suite is included. Unit tests verify BQL query templates against a sample ledger; end-to-end tests verify the full skill + `bean-query` pipeline (requires OpenCode).

```bash
# Unit tests (no LLM calls, fast)
cd tests
python test_queries.py

# End-to-end tests (calls OpenCode + LLM, costs tokens)
python test_e2e.py                        # all 8 tests against sample.beancount
python test_e2e.py --test balance_inquiry # single test
python test_e2e.py --list                 # list all test names
python test_e2e.py /path/to/your/ledger   # run against your real ledger
```

## License

MIT

# BQL Reference

Load this file when constructing complex or custom BQL queries.

## Table of Contents

1. [Query Syntax](#query-syntax)
2. [Available Tables](#available-tables)
3. [Common Columns](#common-columns)
4. [Scalar Functions](#scalar-functions)
5. [Aggregate Functions](#aggregate-functions)
6. [FROM vs WHERE](#from-vs-where)
7. [Shortcut Commands](#shortcut-commands)
8. [CLI Options](#cli-options)

---

## Query Syntax

```sql
SELECT [DISTINCT] [<targets> | *]
[FROM <from_expr> [OPEN ON <date>] [CLOSE [ON <date>]] [CLEAR]]
[WHERE <where_expr>]
[GROUP BY <groups>]
[ORDER BY <columns> [ASC|DESC]]
[LIMIT <num>]
```

Key clauses:
- `OPEN ON <date>` — summarize all transactions before the date into opening balances
- `CLOSE ON <date>` — exclude transactions after the date
- `CLEAR` — transfer final Income/Expenses balances to Equity

Operators:
- `~` — regex match (e.g., `account ~ 'Expenses'`)
- `in` — set membership (e.g., `'tag-name' in tags`)
- `AND`, `OR`, `NOT` — boolean logic
- `=`, `!=`, `<`, `>`, `<=`, `>=` — comparisons

---

## Available Tables

Default table (no FROM clause) is `postings`.

| Table | Description |
|---|---|
| `postings` | All posting legs (default) |
| `transactions` | Transaction directives |
| `entries` | All directive entries |
| `accounts` | Opened accounts |
| `balances` | Balance assertions |
| `commodities` | Commodity/currency directives |
| `prices` | Price directives |
| `events` | Event directives |
| `notes` | Note directives |
| `documents` | Document directives |

---

## Common Columns

### Date & Time

| Column | Type | Notes |
|---|---|---|
| `date` | date | Directive date |
| `year` | int | Shorthand for `year(date)` |
| `month` | int | Shorthand for `month(date)` |
| `day` | int | Shorthand for `day(date)` |

### Transaction Info

| Column | Type | Notes |
|---|---|---|
| `flag` | str | `*`, `!`, or `txn` |
| `payee` | str | Payee field |
| `narration` | str | Narration field |
| `description` | str | Combined `payee | narration` |
| `tags` | set | Transaction tags |
| `links` | set | Transaction links |

### Posting Info

| Column | Type | Notes |
|---|---|---|
| `account` | str | Account name |
| `other_accounts` | set | Other accounts in the same txn |
| `number` | decimal | Numeric amount |
| `currency` | str | Currency of the posting |
| `position` | position | Amount + cost spec |
| `balance` | inventory | Running balance |
| `weight` | amount | Computed weight for balancing |
| `cost_number` | decimal | Cost basis number |
| `cost_currency` | str | Cost basis currency |

### Metadata & Location

| Column | Type | Notes |
|---|---|---|
| `filename` | str | Source file path |
| `lineno` | int | Line number |
| `location` | str | `filename:lineno` |
| `meta` | dict | Posting metadata |
| `id` | str | Unique directive ID |
| `type` | str | Directive type |

---

## Scalar Functions

### Date Functions

| Function | Description |
|---|---|
| `year(date)` | Extract year |
| `month(date)` | Extract month (1-12) |
| `day(date)` | Extract day |
| `quarter(date)` | Extract quarter (1-4) |
| `weekday(date)` | 3-letter weekday name |
| `yearmonth(date)` | Year-month combined value |
| `date(y, m, d)` | Construct date |
| `date_add(date, days)` | Add/subtract days |
| `date_diff(d1, d2)` | Difference in days |
| `date_trunc(precision, date)` | Truncate to precision |
| `today()` | Current date |

### Account Functions

| Function | Description |
|---|---|
| `root(account)` | Top-level account component |
| `root(account, n)` | First n components |
| `parent(account)` | Parent account |
| `leaf(account)` | Last component |
| `account_sortkey(account)` | Sort key respecting account types |
| `open_date(account)` | Open date of the account |
| `close_date(account)` | Close date of the account |

### Amount Functions

| Function | Description |
|---|---|
| `abs(x)` | Absolute value |
| `neg(x)` | Negate |
| `round(x)` / `round(x, n)` | Round to n decimals |
| `safediv(a, b)` | Division, returns 0 on divide-by-zero |
| `number(amount)` | Extract numeric value |
| `currency(amount)` | Extract currency string |
| `units(pos)` | Strip cost, keep units |
| `cost(pos)` | Get cost basis |
| `convert(x, currency)` | Convert to target currency |
| `value(x)` / `value(x, date)` | Market value |
| `filter_currency(inv, cur)` | Filter inventory to one currency |
| `only(currency, inv)` | Get one currency amount from inventory |
| `possign(x, account)` | Correct sign based on account type |

### String Functions

| Function | Description |
|---|---|
| `grep(pattern, string)` | Regex match, return matched portion |
| `grepn(pattern, string, n)` | Regex subgroup match |
| `subst(s, pattern, repl)` | Regex substitution |
| `substr(s, start, len)` | Substring |
| `upper(s)` / `lower(s)` | Case conversion |
| `maxwidth(s, n)` | Truncate with ellipsis |
| `length(x)` | Length of string/list/set |
| `joinstr(set)` | Join set to comma-separated string |
| `findfirst(regex, set)` | First matching element in set |
| `str(x)` / `repr(x)` | String conversion |

### Metadata Functions

| Function | Description |
|---|---|
| `meta(key)` | Posting metadata value |
| `entry_meta(key)` | Transaction metadata value |
| `any_meta(key)` | Posting or parent transaction metadata |
| `open_meta(account)` | All metadata from open directive |
| `open_meta(account, key)` | Specific metadata from open directive |

### Type Conversion

| Function | Description |
|---|---|
| `bool(x)` | Convert to boolean |
| `int(x)` | Convert to integer |
| `decimal(x)` | Convert to decimal |
| `parse_date(s)` | Parse date from string |

---

## Aggregate Functions

Used with `GROUP BY`:

| Function | Description |
|---|---|
| `count(*)` / `count(x)` | Count rows / non-NULL values |
| `sum(x)` | Sum (decimal, amount, position, inventory) |
| `min(x)` / `max(x)` | Minimum / maximum |
| `first(x)` / `last(x)` | First / last value in group |

---

## FROM vs WHERE

- **FROM** filters at the **directive level** (date, flag, payee, narration, tags, links). This preserves the accounting equation for balance reports.
- **WHERE** filters at the **posting level** (account, number, currency, position).

Examples:
```sql
-- FROM: filter by date range (preserves balanced transactions)
SELECT account, sum(position) FROM date >= 2025-01-01 GROUP BY account

-- WHERE: filter by account (only matching postings)
SELECT date, narration, number WHERE account ~ 'Expenses'

-- Combined: date range + account filter
SELECT date, narration, number FROM date >= 2025-01-01 WHERE account ~ 'Expenses'
```

---

## Shortcut Commands

| Command | Description |
|---|---|
| `BALANCES [FROM ...]` | Show account balances |
| `JOURNAL <account-regex> [FROM ...]` | Show register/journal for an account |
| `PRINT [FROM ...]` | Output transactions in beancount format |

---

## CLI Options

```
bean-query [OPTIONS] <filename> [QUERY]

Options:
  -f, --format [text|csv|beancount]   Output format (default: text)
  -o, --output FILENAME               Write output to file
  -m, --numberify                     Strip currencies, output numbers only
  -q, --no-errors                     Suppress ledger validation errors
```

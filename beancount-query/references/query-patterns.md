# Query Patterns

Load this file to match user intent to query templates. Each module lists trigger keywords, query templates with `{param}` placeholders, and usage notes.

## Table of Contents

1. [Account Listing](#1-account-listing)
2. [Balance Inquiry](#2-balance-inquiry)
3. [Net Worth](#3-net-worth)
4. [Expense Analysis](#4-expense-analysis)
5. [Income Analysis](#5-income-analysis)
6. [Trend Analysis](#6-trend-analysis)
7. [Category Ranking](#7-category-ranking)
8. [Transaction Journal](#8-transaction-journal)
9. [Liability Overview](#9-liability-overview)
10. [Budget Inquiry](#10-budget-inquiry)
11. [Custom BQL Query](#11-custom-bql-query)
12. [Data Export](#12-data-export)

---

## 1. Account Listing

**Keywords:** accounts, list accounts, what accounts, 账户, 所有账户, 有哪些账户

### All accounts
```sql
SELECT DISTINCT account ORDER BY account
```

### Filter by account type
```sql
SELECT DISTINCT account WHERE account ~ '{type}' ORDER BY account
```
- `{type}`: `Assets`, `Liabilities`, `Equity`, `Income`, `Expenses`

### Show accounts with open/close dates
```sql
SELECT account, open_date(account) AS opened, close_date(account) AS closed
FROM accounts ORDER BY account
```

---

## 2. Balance Inquiry

**Keywords:** balance, how much, remaining, 余额, 还有多少, 多少钱

### All account balances
```sql
BALANCES
```

### Balances for a specific account type
```sql
SELECT account, sum(position) AS balance
WHERE account ~ '{type}'
GROUP BY account ORDER BY account
```
- `{type}`: `Assets`, `Liabilities`, etc.

### Balance of a specific account
```sql
SELECT account, sum(position) AS balance
WHERE account ~ '{account_pattern}'
GROUP BY account
```
- `{account_pattern}`: regex pattern, e.g., `Bank:Checking`, `Alipay`

### Balances at a specific date
```sql
SELECT account, sum(position) AS balance
FROM date <= {date}
WHERE account ~ '{type}'
GROUP BY account ORDER BY account
```

---

## 3. Net Worth

**Keywords:** net worth, total assets, 净资产, 资产总额, 身价

### Current net worth
```sql
SELECT sum(position) AS net_worth
WHERE account ~ 'Assets|Liabilities'
```

### Net worth breakdown
```sql
SELECT root(account, 1) AS type, sum(position) AS total
WHERE account ~ 'Assets|Liabilities'
GROUP BY root(account, 1)
```

### Net worth at a specific date
```sql
SELECT sum(position) AS net_worth
FROM date <= {date}
WHERE account ~ 'Assets|Liabilities'
```

---

## 4. Expense Analysis

**Keywords:** expenses, spending, how much spent, cost, 支出, 花了多少, 消费, 开销

### Total expenses for a period
```sql
SELECT sum(number) AS total
WHERE account ~ 'Expenses'
  AND date >= {start_date} AND date < {end_date}
```

### Expenses by category for a period
```sql
SELECT account, sum(number) AS total
WHERE account ~ 'Expenses'
  AND date >= {start_date} AND date < {end_date}
GROUP BY account ORDER BY total DESC
```

### Expenses by sub-category (leaf level)
```sql
SELECT leaf(account) AS category, sum(number) AS total
WHERE account ~ 'Expenses:{parent_category}'
  AND date >= {start_date} AND date < {end_date}
GROUP BY leaf(account) ORDER BY total DESC
```
- `{parent_category}`: e.g., `Food`, `Transport`, `Education`

### This month's expenses
```sql
SELECT account, sum(number) AS total
WHERE account ~ 'Expenses'
  AND year = {current_year} AND month = {current_month}
GROUP BY account ORDER BY total DESC
```

### Specific category expenses
```sql
SELECT date, narration, number, currency
WHERE account ~ '{category_pattern}'
  AND date >= {start_date} AND date < {end_date}
ORDER BY date
```

---

## 5. Income Analysis

**Keywords:** income, salary, earnings, 收入, 工资, 赚了多少

### Total income for a period
```sql
SELECT sum(number) AS total
WHERE account ~ 'Income'
  AND date >= {start_date} AND date < {end_date}
```
Note: Income amounts are typically negative in beancount. Use `neg(sum(number))` or `abs(sum(number))` to show as positive.

### Income by source
```sql
SELECT account, neg(sum(number)) AS total
WHERE account ~ 'Income'
  AND date >= {start_date} AND date < {end_date}
GROUP BY account ORDER BY total DESC
```

### Annual income
```sql
SELECT year, neg(sum(number)) AS total
WHERE account ~ 'Income'
GROUP BY year ORDER BY year
```

---

## 6. Trend Analysis

**Keywords:** trend, monthly, yearly, over time, compare, 趋势, 每月, 每年, 对比, 变化

### Monthly expense trend
```sql
SELECT year, month, sum(number) AS total
WHERE account ~ 'Expenses'
  AND date >= {start_date}
GROUP BY year, month ORDER BY year, month
```

### Monthly expense trend for a specific year
```sql
SELECT month, sum(number) AS total
WHERE account ~ 'Expenses' AND year = {year}
GROUP BY month ORDER BY month
```

### Yearly expense comparison
```sql
SELECT year, sum(number) AS expenses
WHERE account ~ 'Expenses'
GROUP BY year ORDER BY year
```

### Monthly trend for a specific category
```sql
SELECT year, month, sum(number) AS total
WHERE account ~ '{category_pattern}'
  AND date >= {start_date}
GROUP BY year, month ORDER BY year, month
```

### Quarterly summary
```sql
SELECT year, quarter(date) AS quarter, sum(number) AS total
WHERE account ~ 'Expenses'
  AND year = {year}
GROUP BY year, quarter(date) ORDER BY year, quarter(date)
```

---

## 7. Category Ranking

**Keywords:** top, most, biggest, ranking, largest, 最多, 排名, 最大, 哪个类别

### Top expense categories (all time)
```sql
SELECT account, sum(number) AS total
WHERE account ~ 'Expenses'
GROUP BY account ORDER BY total DESC LIMIT {n}
```

### Top expenses for a period
```sql
SELECT account, sum(number) AS total
WHERE account ~ 'Expenses'
  AND date >= {start_date} AND date < {end_date}
GROUP BY account ORDER BY total DESC LIMIT {n}
```

### Largest single transactions
```sql
SELECT date, narration, account, number, currency
WHERE account ~ 'Expenses'
ORDER BY number DESC LIMIT {n}
```

### Most frequent expense categories
```sql
SELECT account, count(*) AS frequency
WHERE account ~ 'Expenses'
GROUP BY account ORDER BY frequency DESC LIMIT {n}
```

### Top expense categories by leaf name
```sql
SELECT leaf(account) AS category, sum(number) AS total
WHERE account ~ 'Expenses'
GROUP BY leaf(account) ORDER BY total DESC LIMIT {n}
```

---

## 8. Transaction Journal

**Keywords:** transactions, journal, recent, history, 流水, 交易, 最近, 明细, 记录

### Recent transactions (all accounts)
```sql
SELECT date, narration, account, number, currency
ORDER BY date DESC LIMIT {n}
```

### Journal for a specific account
```sql
JOURNAL '{account_pattern}' FROM date >= {start_date}
```

### Transactions for an account in a date range
```sql
SELECT date, narration, number, currency, other_accounts
WHERE account ~ '{account_pattern}'
  AND date >= {start_date} AND date < {end_date}
ORDER BY date
```

### Search transactions by narration
```sql
SELECT date, narration, account, number, currency
WHERE narration ~ '{search_term}'
ORDER BY date DESC
```

### Transactions with a specific payee
```sql
SELECT date, payee, narration, account, number, currency
WHERE payee ~ '{payee_pattern}'
ORDER BY date DESC
```

---

## 9. Liability Overview

**Keywords:** debt, liability, owe, mortgage, credit card, 负债, 欠, 房贷, 信用卡, 花呗, 白条

### All liabilities
```sql
SELECT account, sum(position) AS balance
WHERE account ~ 'Liabilities'
GROUP BY account ORDER BY account
```

### Specific liability balance
```sql
SELECT account, sum(position) AS balance
WHERE account ~ '{liability_pattern}'
GROUP BY account
```
- `{liability_pattern}`: e.g., `Mortgage`, `CreditCard:Chase`, `StudentLoan`

### Liability payment history
```sql
SELECT date, narration, number, currency
WHERE account ~ '{liability_pattern}'
  AND number > 0
ORDER BY date DESC LIMIT {n}
```

### Total debt
```sql
SELECT neg(sum(position)) AS total_debt
WHERE account ~ 'Liabilities'
```

---

## 10. Budget Inquiry

**Keywords:** budget, allocation, 预算, 分配

### Budget allocations
```sql
SELECT account, sum(position) AS allocated
WHERE account ~ 'Equity:Budget'
GROUP BY account ORDER BY account
```

### Specific budget category
```sql
SELECT account, sum(position) AS allocated
WHERE account ~ 'Equity:Budget:{budget_category}'
GROUP BY account
```

---

## 11. Custom BQL Query

**Keywords:** query, BQL, run, execute, 执行查询, 运行

Directly execute the user-provided BQL string. Before execution:
1. Verify the query is syntactically reasonable (SELECT/BALANCES/JOURNAL/PRINT)
2. Ensure it is read-only (no directives that modify data)
3. Execute as-is with `bean-query`

---

## 12. Data Export

**Keywords:** export, CSV, download, save, 导出, 保存

### Export to CSV
Use `-f csv` flag:
```bash
bean-query -f csv {ledger_file} "{query}" -o {output_file}
```

### Export with numbers only (no currency symbols)
```bash
bean-query -f csv -m {ledger_file} "{query}" -o {output_file}
```

### Common export queries

Export all transactions:
```sql
SELECT date, flag, narration, account, number, currency ORDER BY date
```

Export expense summary:
```sql
SELECT account, sum(number) AS total WHERE account ~ 'Expenses' GROUP BY account ORDER BY total DESC
```

Export monthly totals:
```sql
SELECT year, month, sum(number) AS total WHERE account ~ 'Expenses' GROUP BY year, month ORDER BY year, month
```

---

## Parameter Reference

| Placeholder | Description | Examples |
|---|---|---|
| `{type}` | Account type | `Assets`, `Liabilities`, `Income`, `Expenses`, `Equity` |
| `{account_pattern}` | Regex for account name | `Bank:Checking`, `Assets:.*Bank`, `CreditCard` |
| `{category_pattern}` | Regex for expense/income category | `Expenses:Food`, `Expenses:Transport` |
| `{start_date}` | Start date (inclusive) | `2025-01-01` |
| `{end_date}` | End date (exclusive) | `2025-02-01` |
| `{date}` | Specific date | `2025-06-15` |
| `{year}` | Year number | `2025` |
| `{current_year}` | Current year | Use `year` column directly |
| `{current_month}` | Current month | Use `month` column directly |
| `{n}` | Row limit | `5`, `10`, `20` |
| `{search_term}` | Narration search regex | `grocery`, `rent` |
| `{payee_pattern}` | Payee search regex | Any payee name |
| `{liability_pattern}` | Liability account regex | `Mortgage`, `CreditCard:Chase` |
| `{budget_category}` | Budget category name | `Travel`, `Electronics`, `Education` |
| `{ledger_file}` | Path to beancount file | Determined by skill workflow |
| `{output_file}` | Export output path | `export.csv`, `monthly.csv` |

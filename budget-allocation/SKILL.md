---
name: budget-allocation
description: >-
  Generate monthly budget allocation and spending entries for beancount ledger.
  Use this skill when the user asks to generate or allocate/apply monthly budget at or create next month's budget,
  or when keywords include: 预算, 分配预算, 生成本月预算, 下月预算.
  budget allocation.
---

# Monthly Budget Allocation

Generate monthly budget allocation entries for beancount ledger at the end of each month.

## Workflow

For each monthly budget generation, follow these steps:

1. **Determine the target month** — The current month's last day for the allocation date. Use today's date to determine the target month. For example, if today is 2026-03-31, the target month is 2026-03. If today is 2026-04-30, the target month is 2026-04.
2. **Query current budget balances** — Run the following to get all budget account balances:
   ```bash
   bean-query -q <ledger_file> "SELECT account, sum(number) AS balance WHERE account ~ 'Equity:Budget' AND NOT account ~ 'Z已分配' GROUP BY account ORDER BY account"
   ```
3. **Query current month's expenses by category** — Run the following to calculate spending for each budget category:
   ```bash
   bean-query -q <ledger_file> "SELECT root(account, 3) AS category, sum(number) AS total WHERE account ~ 'Expenses' AND date >= DATE('<target_month>-01') AND date < DATE('<target_month_last_day>') + 1 GROUP BY root(account, 3) ORDER BY total DESC"
   ```
4. **Generate spending entry** — For each category with expenses, create a negative entry:
   ```beancount
   YYYY-MM-DD * "预算" "花费"
    Equity:Budget:交通              -XXX.XX CNY
    Equity:Budget:孩子教育            -XXX.XX CNY
    Equity:Budget:Z已分配
   ```
5. **Check 数码 budget limit** — If 数码 account balance > 40,000, skip allocation and add a recovery entry:
   ```beancount
   YYYY-MM-DD * "预算" "数码预算超出上限40000,回收多余部分"
    Equity:Budget:数码                                  -<excess_amount> CNY
    Equity:Budget:Z已分配
   ```
6. **Generate allocation entry** — Create positive entries using the standard allocation template below. Adjust allocations based on step 5 checks results.

## Standard Monthly Allocation

| Category | Monthly Amount                     |
| -------- | ---------------------------------- |
| 保险     | 3,500.00 CNY                       |
| 投资     | 2,000.00 CNY                       |
| 自我提高 | 500.00 CNY                         |
| 孩子教育 | 1,000.00 CNY                       |
| 旅游健康 | 1,500.00 CNY                       |
| 交通     | 4,500.00 CNY                       |
| 数码     | 1,000.00 CNY (only if below limit) |

Total monthly allocation: **14,000.00 CNY** (or 13,000.00 CNY if digital skipped)

## 数码 Category Rules

- Budget limit: **40,000.00 CNY**
- When monthly balance exceeds limit: skip allocation and recover excess
- When balance drops below limit: resume normal allocation (1,000.00 CNY/month)

## 交通 Category Rules

- Budget limit: **300,000.00 CNY**
- When monthly balance exceeds limit: skip allocation and recover excess
- When balance drops below limit: resume normal allocation (4,500.00 CNY/month)
- **车险从交通预算里扣除**，不使用保险预算

## 花费核销规则

- Expenses:R日常:交通 → Equity:Budget:交通
- Expenses:C车:加油 → Equity:Budget:交通
- Expenses:C车:使用 → Equity:Budget:交通（车险从交通扣）
- Expenses:H孩子教育:* → Equity:Budget:孩子教育
- Expenses:X学习:* → Equity:Budget:自我提高

## Output Format

```beancount
YYYY-MM-DD * "预算" "花费"
  Equity:Budget:交通              -<transport_spending> CNY
  Equity:Budget:孩子教育            -<education_spending> CNY
  Equity:Budget:Z已分配

YYYY-MM-DD * "预算" "分配"
  Equity:Budget:保险                              3500.00 CNY
  Equity:Budget:投资                              2000.00 CNY
  Equity:Budget:自我提高                                500.00 CNY
  Equity:Budget:孩子教育                            1000.00 CNY
  Equity:Budget:旅游健康                              1500.00 CNY
  Equity:Budget:交通                              4500.00 CNY
  Equity:Budget:Z已分配
```

## Safety Constraints

- **Read-only on ledger structure**: Do not modify existing transactions, only append new budget entries at the end of the month.
- **Always run bean-check** after generating entries to validate balance.

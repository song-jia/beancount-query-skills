---
name: add-transaction
description: >
  Add transaction entries to beancount ledger files. Use when the user wants to record
  expenses, income, transfers, credit card payments, or any financial transaction.
  Triggers: 记账, 添加交易, 添加记录, 记一笔, 录入, 记录消费, 记录支出, 记录收入,
  还款, 转账, add transaction, record expense. Also use when the user mentions a purchase,
  payment, or financial activity they want recorded in the ledger.
---

# Add Transaction

Insert transaction entries via `scripts/insert_txn.py`.

## Quick Reference

### Script Usage

```bash
python3 scripts/insert_txn.py LEDGER_FILE \
  --date YYYY-MM-DD \
  --payee CATEGORY \
  --narration DESCRIPTION \
  --posting "ACCOUNT [AMOUNT CNY]" \
  [--posting ...] \
  [--dry-run] [--flag *]
```

- `--posting` is repeatable. First posting = debit side with amount; second = credit side (omit amount for auto-balance).
- `--dry-run` prints without modifying.
- Account aliases supported (e.g., `招行`, `工行126`, `现金`); see `references/accounts.md` for full list.
- Script auto-locates insertion point by date, inserts, runs `bean-check`, and rolls back on failure.

### Transaction Templates

**Expense**: `--payee "日常" --narration "DESC" --posting "Expenses:R日常:SUBCAT AMT CNY" --posting "PAYMENT"`
**Income**: `--payee "收入" --narration "DESC" --posting "ASSET AMT CNY" --posting "Income:TYPE"`
**Payment**: `--payee "还款" --narration "还BANK信用卡" --posting "Liabilities:X信用卡:BANK:CARD AMT CNY" --posting "SOURCE"`
**Transfer**: `--payee "转账" --narration "DESC" --posting "TO_ACCOUNT AMT CNY" --posting "FROM_ACCOUNT"`
**Housing fund**: `--payee "收入" --narration "公积金" --posting "Assets:G公积金 AMT CNY" --posting "Income:1工资"`

## Workflow

1. Parse user intent → date, type, amount, description, payment method.
2. Resolve accounts (use aliases or full names from `references/accounts.md`).
3. Categorize expenses by keyword (吃饭→日常:吃饭, 加油→车:加油, etc.).
4. Run `insert_txn.py` with `--dry-run` first if unsure.
5. Run without `--dry-run` to insert. Script validates and reports result.
6. For batch entries, run the script once per transaction.

## Expense Category Keywords

| Keywords | Account |
|----------|---------|
| 吃饭/餐/外卖/奶茶/咖啡/水果 | `Expenses:R日常:吃饭` |
| 打车/地铁/公交 | `Expenses:R日常:交通` |
| 加油 | `Expenses:C车:加油` |
| 停车/过路费/ETC | `Expenses:C车:使用` |
| 保养/维修 | `Expenses:C车:维修保养` |
| 衣服/鞋/包 | `Expenses:R日常:穿戴` |
| 手机/电脑/耳机/数码 | `Expenses:R日常:数码` |
| 话费/流量/宽带 | `Expenses:R日常:通讯` |
| 旅游/酒店/机票 | `Expenses:R日常:旅行` |
| 保险/寿险 | `Expenses:B保险` |
| 看病/药/体检 | `Expenses:Y医疗` |
| 书/课程 | `Expenses:X学习` |
| 物业/水电/燃气 | `Expenses:R日常:物业` |
| 休闲/娱乐/游戏 | `Expenses:R日常:休闲` |
| Default | `Expenses:R日常:其他` |

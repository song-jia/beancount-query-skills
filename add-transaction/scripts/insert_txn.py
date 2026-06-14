#!/usr/bin/env python3
"""Insert a transaction into a beancount ledger file.

Usage:
    # Expense
    insert_txn general.beancount --date 2026-06-08 --payee 日常 --narration 午饭 \
        --posting "Expenses:R日常:吃饭 25.00 CNY" \
        --posting "Liabilities:X信用卡:招行:4763"

    # Credit card payment
    insert_txn general.beancount --date 2026-06-08 --payee 还款 --narration 还招行信用卡 \
        --posting "Liabilities:X信用卡:招行:4763 5000.00 CNY" \
        --posting "Assets:G工商银行:049"

    # Dry run (print without modifying)
    insert_txn general.beancount --dry-run --date 2026-06-08 --payee 日常 --narration 午饭 \
        --posting "Expenses:R日常:吃饭 25.00 CNY" \
        --posting "Liabilities:X信用卡:招行:4763"
"""

import argparse
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path

# Account aliases: short name → full account name
ALIASES = {
    # Credit cards
    "招行": "Liabilities:X信用卡:招行:4763",
    "招商": "Liabilities:X信用卡:招行:4763",
    "中信": "Liabilities:X信用卡:中信:2895",
    "广发": "Liabilities:X信用卡:广发:3861",
    "花呗": "Liabilities:M蚂蚁花呗",
    "京东白条": "Liabilities:J京东白条",
    # Bank accounts
    "工行049": "Assets:G工商银行:049",
    "工行126": "Assets:G工商银行:126",
    "建行": "Assets:J建设银行:502",
    "农行": "Assets:N农业银行:575",
    "微信": "Assets:W微信钱包",
    "余额宝": "Assets:Z支付宝:余额宝",
    "现金": "Assets:X现金",
    "公积金": "Assets:G公积金",
    # Income
    "工资": "Income:1工资",
    "利息": "Income:1利息收益",
    "红包": "Income:2红包",
    "兼职": "Income:3兼职",
    "报销": "Income:4报销",
    "投资收益": "Income:6投资收益",
}

# Expense keywords → account
EXPENSE_KEYWORDS = [
    (["吃饭", "餐", "外卖", "奶茶", "咖啡", "早餐", "午餐", "晚餐", "水果", "零食"], "Expenses:R日常:吃饭"),
    (["加油"], "Expenses:C车:加油"),
    (["停车", "过路费", "ETC"], "Expenses:C车:使用"),
    (["保养", "维修"], "Expenses:C车:维修保养"),
    (["打车", "地铁", "公交", "高铁", "火车"], "Expenses:R日常:交通"),
    (["衣服", "鞋", "包"], "Expenses:R日常:穿戴"),
    (["手机", "电脑", "耳机", "数码"], "Expenses:R日常:数码"),
    (["话费", "流量", "宽带"], "Expenses:R日常:通讯"),
    (["旅游", "酒店", "机票"], "Expenses:R日常:旅行"),
    (["保险", "寿险"], "Expenses:B保险"),
    (["看病", "药", "体检", "医疗"], "Expenses:Y医疗"),
    (["书", "课程"], "Expenses:X学习"),
    (["物业", "水电", "燃气"], "Expenses:R日常:物业"),
    (["休闲", "娱乐", "游戏"], "Expenses:R日常:休闲"),
]


def resolve_alias(name: str) -> str:
    """Resolve an account alias to its full name."""
    return ALIASES.get(name, name)


def resolve_expense(keyword: str) -> str | None:
    """Try to match a keyword to an expense account."""
    for keywords, account in EXPENSE_KEYWORDS:
        if any(k in keyword for k in keywords):
            return account
    return None


def find_insert_position(lines: list[str], target_date: str) -> int:
    """Find the line index to insert a transaction.

    For same-date entries, inserts after the LAST entry with that date.
    For earlier dates, inserts after all entries on or before that date.
    """
    best = -1
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith(";"):
            continue
        # Match date at start of line: YYYY-MM-DD
        if len(stripped) >= 10 and stripped[4] == "-" and stripped[7] == "-":
            try:
                line_date = stripped[:10]
                if line_date <= target_date:
                    best = i
            except (ValueError, IndexError):
                continue

    # Walk past blank lines AND continuation lines (indented) after best date header
    insert_at = best + 1
    # First skip postings (indented lines) of the last transaction
    while insert_at < len(lines) and lines[insert_at].startswith("  "):
        insert_at += 1
    # Then skip the blank line separator
    while insert_at < len(lines) and lines[insert_at].strip() == "":
        insert_at += 1

    return insert_at


def format_transaction(date: str, flag: str, payee: str, narration: str, postings: list[str]) -> str:
    """Format a beancount transaction string."""
    header = f'{date} {flag} "{payee}" "{narration}"'
    formatted_postings = []
    for p in postings:
        parts = p.strip().split(None, 1)
        account = resolve_alias(parts[0])
        if len(parts) > 1:
            formatted_postings.append(f"  {account}  {parts[1]}")
        else:
            formatted_postings.append(f"  {account}")
    return header + "\n" + "\n".join(formatted_postings) + "\n"


def run_bean_check(filepath: str) -> tuple[bool, str]:
    """Run bean-check and return (success, output)."""
    result = subprocess.run(
        ["bean-check", filepath],
        capture_output=True, text=True, timeout=30
    )
    output = result.stdout + result.stderr
    return result.returncode == 0, output.strip()


def insert_transaction(filepath: str, date: str, flag: str, payee: str,
                       narration: str, postings: list[str], dry_run: bool = False) -> None:
    """Insert a transaction into the ledger file."""
    txn_text = format_transaction(date, flag, payee, narration, postings)

    if dry_run:
        print(f"[DRY RUN] Would insert after entries with date ≤ {date}:")
        print()
        print(txn_text)
        return

    # Read the file
    path = Path(filepath)
    content = path.read_text(encoding="utf-8")
    lines = content.split("\n")

    # Remove trailing empty line if present (we'll add it back)
    if lines and lines[-1] == "":
        lines = lines[:-1]

    # Find insertion point
    insert_at = find_insert_position(lines, date)

    # Insert: ensure blank line before and after the transaction
    txn_lines = txn_text.split("\n")

    # Check if there's a blank line before insert_at
    need_blank_before = insert_at > 0 and lines[insert_at - 1].strip() != ""
    if need_blank_before:
        txn_lines.insert(0, "")

    # Check if there's a blank line after the inserted block
    need_blank_after = insert_at < len(lines) and lines[insert_at].strip() != ""
    if need_blank_after:
        txn_lines.append("")

    for i, line in enumerate(txn_lines):
        lines.insert(insert_at + i, line)

    # Ensure trailing newline and blank line separator
    new_content = "\n".join(lines) + "\n"

    # Write to temp file first, validate, then move
    backup = path.with_suffix(".beancount.bak")
    shutil.copy2(path, backup)

    try:
        path.write_text(new_content, encoding="utf-8")
        success, output = run_bean_check(str(path))

        if success:
            backup.unlink()
            print(f"✅ Transaction inserted and validated:")
            print()
            print(txn_text)
        else:
            # Rollback
            shutil.copy2(backup, path)
            backup.unlink()
            print(f"❌ bean-check failed, rolled back:", file=sys.stderr)
            print(output, file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        # Ensure rollback on any error
        shutil.copy2(backup, path)
        if backup.exists():
            backup.unlink()
        raise


def main():
    parser = argparse.ArgumentParser(description="Insert a beancount transaction")
    parser.add_argument("file", help="Path to the beancount ledger file")
    parser.add_argument("--date", required=True, help="Transaction date (YYYY-MM-DD)")
    parser.add_argument("--flag", default="*", help="Transaction flag (default: *)")
    parser.add_argument("--payee", required=True, help="Payee / category tag")
    parser.add_argument("--narration", required=True, help="Transaction description")
    parser.add_argument("--posting", action="append", required=True,
                        help='Posting in format "account [amount currency]". Use multiple --posting flags.')
    parser.add_argument("--dry-run", action="store_true", help="Print without modifying")
    args = parser.parse_args()

    insert_transaction(args.file, args.date, args.flag, args.payee, args.narration,
                       args.posting, args.dry_run)


if __name__ == "__main__":
    main()

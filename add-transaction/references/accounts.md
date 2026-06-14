# Account Reference

## Expense Accounts (Expenses)

| Category | Account | Chinese |
|----------|---------|---------|
| Daily - Transport | `Expenses:R日常:交通` | 日常-交通 |
| Daily - Food | `Expenses:R日常:吃饭` | 日常-吃饭 |
| Daily - Shopping | `Expenses:R日常:其他` | 日常-其他(购物等) |
| Daily - Digital | `Expenses:R日常:数码` | 日常-数码 |
| Daily - Clothing | `Expenses:R日常:穿戴` | 日常-穿戴 |
| Daily - Telecom | `Expenses:R日常:通讯` | 日常-通讯 |
| Daily - Leisure | `Expenses:R日常:休闲` | 日常-休闲 |
| Daily - Travel | `Expenses:R日常:旅行` | 日常-旅行 |
| Daily - Property | `Expenses:R日常:物业` | 日常-物业 |
| Car - Purchase | `Expenses:C车:买车` | 车-买车 |
| Car - Gas | `Expenses:C车:加油` | 车-加油 |
| Car - Maintenance | `Expenses:C车:维修保养` | 车-维修保养 |
| Car - Usage | `Expenses:C车:使用` | 车-使用(停车/过路费等) |
| Child Education - School | `Expenses:H孩子教育:学校` | 孩子教育-学校 |
| Child Education - Tools | `Expenses:H孩子教育:工具` | 孩子教育-工具 |
| Child Education - Tutoring | `Expenses:H孩子教育:课外辅导` | 孩子教育-课外辅导 |
| Education | `Expenses:X学习` | 学习 |
| Education - Books | `Expenses:X学习:书` | 学习-书 |
| Insurance | `Expenses:B保险` | 保险 |
| Medical | `Expenses:Y医疗` | 医疗 |
| Investment Loss | `Expenses:T投资亏损` | 投资亏损 |

## Payment Accounts (Assets / Liabilities)

### Credit Cards
| Account | Chinese |
|---------|---------|
| `Liabilities:X信用卡:招行:4763` | 招行4763 |
| `Liabilities:X信用卡:中信:2895` | 中信2895 |
| `Liabilities:X信用卡:广发:3861` | 广发3861 |

### Other Payment Liabilities
| Account | Chinese |
|---------|---------|
| `Liabilities:M蚂蚁花呗` | 花呗 |
| `Liabilities:J京东白条` | 京东白条 |

### Bank / Asset Accounts
| Account | Chinese |
|---------|---------|
| `Assets:G工商银行:049` | 工行049 |
| `Assets:G工商银行:126` | 工行126 |
| `Assets:J建设银行:502` | 建行502 |
| `Assets:N农业银行:575` | 农行575 |
| `Assets:N农业银行:借记卡` | 农行借记卡 |
| `Assets:W微信钱包` | 微信 |
| `Assets:X现金` | 现金 |
| `Assets:Z支付宝:余额宝` | 余额宝 |
| `Assets:G公积金` | 公积金 |
| `Assets:P平安证券` | 平安证券 |
| `Assets:T泰康步步高终身寿险` | 泰康寿险 |

## Income Accounts

| Account | Chinese |
|---------|---------|
| `Income:1工资` | 工资 |
| `Income:1利息收益` | 利息收益 |
| `Income:2红包` | 红包 |
| `Income:3兼职` | 兼职 |
| `Income:4报销` | 报销 |
| `Income:5回收旧物` | 回收旧物 |
| `Income:6投资收益` | 投资收益 |

## Common Account Aliases (for fuzzy matching)

User input → Account mapping:
- 招行/招商 → `Liabilities:X信用卡:招行:4763`
- 中信 → `Liabilities:X信用卡:中信:2895`
- 广发 → `Liabilities:X信用卡:广发:3861`
- 花呗 → `Liabilities:M蚂蚁花呗`
- 京东白条 → `Liabilities:J京东白条`
- 工行049/工商银行049 → `Assets:G工商银行:049`
- 工行126/工商银行126 → `Assets:G工商银行:126`
- 建行 → `Assets:J建设银行:502`
- 农行 → `Assets:N农业银行:575`
- 微信 → `Assets:W微信钱包`
- 余额宝 → `Assets:Z支付宝:余额宝`
- 现金 → `Assets:X现金`
- 公积金 → `Assets:G公积金`

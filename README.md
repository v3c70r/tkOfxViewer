# ofxtool

![Application screenshot](https://raw.githubusercontent.com/v3c70r/tkOfxViewer/refs/heads/main/screenshots/screenshot.png)

CLI toolkit for inspecting OFX (Open Financial Exchange) files. Designed for both human and agentic use. Also includes the original tkOfxViewer GUI.

## Install

```bash
pip install -r requirements.txt
```

## Usage

### Quick summary

```bash
python ofxtool.py statement.ofx
python ofxtool.py folder/with/ofx/files/
python ofxtool.py a.ofx b.ofx
```

### Account info and date range

```bash
# Human readable
python ofxtool.py info statement.ofx
python ofxtool.py info folder/

# Agent readable (JSON)
python ofxtool.py info statement.ofx --format json
```

Outputs: account number, routing number, institution, account type, currency, statement period, transaction date range, ledger balance, available balance, transaction count.

### Transactions

```bash
# Human readable table
python ofxtool.py trans statement.ofx
python ofxtool.py trans folder/                    # merged from all files
python ofxtool.py trans a.ofx b.ofx --limit 10     # first 10 across all files
python ofxtool.py trans a.ofx --sort amount --reverse

# Agent readable
python ofxtool.py trans statement.ofx --format json
python ofxtool.py trans folder/ --format csv
```

When multiple files are provided, an **Account** column identifies each transaction's source.

### GUI viewer

```bash
python ofxtool.py view statement.ofx
```

Or use the original standalone GUI:

```bash
python tkOfxViewer.py statement.ofx
```

## Agent instructions

This tool is designed to be called by coding agents for OFX file reconciliation. Use these patterns:

### Get account metadata for reconciliation matching

```bash
python ofxtool.py info path/to/statement.ofx --format json
```

Returns JSON with `account_number`, `routing_number`, `institution`, `statement_period`, `ledger_balance`, `available_balance`, and `transaction_count`.

### Get all transactions for matching

```bash
python ofxtool.py trans path/to/statement.ofx --format json
```

Returns JSON with per-file account metadata and transaction arrays. Each transaction has: `fitid`, `type`, `date`, `payee`, `memo`, `amount`, `checknum`.

### Inspect a folder of OFX files at once

```bash
python ofxtool.py info folder/ --format json
python ofxtool.py trans folder/ --format json
```

The tool recursively finds all `.ofx` files in a directory. Multiple files are returned as a JSON array, one entry per file.

### Filter and sort transactions

```bash
python ofxtool.py trans folder/ --format json --sort date --reverse --limit 50
```

### CSV export for spreadsheet analysis

```bash
python ofxtool.py trans statement.ofx --format csv
```

## Example output

### `info --format json`

```json
{
  "account_number": "4017322224",
  "routing_number": "0614",
  "institution": "Tangerine",
  "institution_fid": "061400152",
  "account_type": "SAVINGS",
  "currency": "CAD",
  "statement_period": { "start": "2024-05-19", "end": "2024-08-17" },
  "ledger_balance": 37.90,
  "available_balance": 37.90,
  "transaction_count": 9
}
```

### `trans --format json`

```json
{
  "file": "statement.ofx",
  "account": { "account_number": "4017322224", ... },
  "transactions": [
    {
      "fitid": "162",
      "type": "credit",
      "date": "2024-06-03",
      "payee": "Internet Deposit from Tangerine",
      "memo": "Completed transfer from Tangerine SAV ...",
      "amount": 400.00,
      "checknum": null
    }
  ]
}
```

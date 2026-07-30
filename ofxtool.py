#!/usr/bin/env python3
"""OFX Toolkit - Inspect OFX financial files for reconciliation.

Usage:
  ofxtool.py info <files...>         Account info, date range, balances
  ofxtool.py trans <files...>        Merged transactions from all files
  ofxtool.py view <file>             GUI viewer (single file)
  ofxtool.py <files...>              Quick summary (no subcommand needed)
"""

import argparse
import csv
import json
import os
import sys
import warnings
from datetime import date
from decimal import Decimal
from parser import AccountInfo, OfxParserWrapper, OfxResult

warnings.filterwarnings("ignore", category=Warning)


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (Decimal,)):
            return float(obj)
        if isinstance(obj, (date,)):
            return str(obj)
        return super().default(obj)


def format_table(headers, rows):
    if not rows:
        return ""
    col_widths = [len(h) for h in headers]
    str_rows = [[str(c) for c in row] for row in rows]
    for row in str_rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(cell))
    sep = "  "
    header_line = sep.join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    lines = [header_line, "-" * len(header_line)]
    for row in str_rows:
        lines.append(sep.join(cell.ljust(col_widths[i]) for i, cell in enumerate(row)))
    return "\n".join(lines)


def collect_ofx_files(paths):
    """Resolve a list of paths into a flat list of .ofx file paths."""
    files = []
    for p in paths:
        if os.path.isdir(p):
            for root, _dirs, filenames in os.walk(p):
                for f in filenames:
                    if f.lower().endswith('.ofx'):
                        files.append(os.path.join(root, f))
        elif os.path.isfile(p) and p.lower().endswith('.ofx'):
            files.append(p)
        elif os.path.isfile(p):
            err(f"Not an OFX file: {p}")
    if not files:
        err("No .ofx files found in the given paths")
    return sorted(files)


def load_ofx(file_path):
    try:
        return OfxParserWrapper(file_path).parse()
    except FileNotFoundError:
        err(f"File not found: {file_path}")
    except Exception as e:
        err(f"Failed to parse {file_path}: {e}")


def err(msg):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def merge_accounts(datasets):
    """Group datasets by account number and merge same-account files."""
    groups = {}
    for data in datasets:
        key = data.account.account_number
        if key not in groups:
            groups[key] = []
        groups[key].append(data)

    merged = []
    for items in groups.values():
        if len(items) == 1:
            merged.append(items[0])
            continue

        all_txns = []
        files = []
        start_dates = []
        end_dates = []
        institution = ''
        institution_fid = ''
        account_type = ''

        for d in items:
            all_txns.extend(d.transactions)
            files.append(d.file_path)
            if d.account.start_date:
                start_dates.append(d.account.start_date)
            if d.account.end_date:
                end_dates.append(d.account.end_date)
            if d.account.institution and not institution:
                institution = d.account.institution
            if d.account.institution_fid and not institution_fid:
                institution_fid = d.account.institution_fid
            if d.account.account_type and not account_type:
                account_type = d.account.account_type

        all_txns.sort(key=lambda t: t.date or date.min)

        items_by_end = sorted(
            (d for d in items if d.account.end_date),
            key=lambda d: d.account.end_date,
        )
        latest = items_by_end[-1].account if items_by_end else items[0].account

        merged_acct = AccountInfo(
            account_number=items[0].account.account_number,
            routing_number=items[0].account.routing_number,
            institution=institution or items[0].account.institution,
            institution_fid=institution_fid or items[0].account.institution_fid,
            account_type=account_type or items[0].account.account_type,
            branch_id=items[0].account.branch_id,
            currency=items[0].account.currency,
            start_date=min(start_dates) if start_dates else None,
            end_date=max(end_dates) if end_dates else None,
            ledger_balance=latest.ledger_balance,
            available_balance=latest.available_balance,
            transaction_count=len(all_txns),
        )

        merged.append(OfxResult(
            file_path=files[0],
            account=merged_acct,
            transactions=all_txns,
            source_files=files,
        ))

    return merged


def fmt_info_block(data, idx=0, total=0):
    """Format a single account info block as text lines."""
    acct = data.account
    txns = data.transactions
    n_files = len(data.source_files)
    lines = []

    if total > 1:
        label = f"{n_files} files" if n_files > 1 else os.path.basename(data.source_files[0])
        lines.append(f"--- [{idx + 1}/{total}] {label} ---")

    if n_files > 1:
        lines.append(f"Source files ({n_files}):")
        for f in data.source_files:
            lines.append(f"  {f}")

    lines += [
        f"Institution:        {acct.institution}",
        f"Account Number:     {acct.account_number}",
    ]
    if acct.routing_number:
        lines.append(f"Routing Number:     {acct.routing_number}")
    if acct.account_type:
        lines.append(f"Account Type:       {acct.account_type}")
    lines += [
        f"Currency:           {acct.currency}",
        f"Statement Period:   {acct.start_date}  to  {acct.end_date}",
    ]
    if txns:
        dates = sorted(t.date for t in txns if t.date)
        if dates:
            lines.append(f"Transaction Range:  {dates[0]}  to  {dates[-1]}")
    if acct.ledger_balance is not None:
        lines.append(f"Ledger Balance:     {acct.ledger_balance} {acct.currency}")
    if acct.available_balance is not None:
        lines.append(f"Available Balance:  {acct.available_balance} {acct.currency}")
    lines.append(f"Transaction Count:  {acct.transaction_count}")
    return "\n".join(lines)


def cmd_info(args):
    ofx_files = collect_ofx_files(args.files)
    datasets = [load_ofx(f) for f in ofx_files]
    merged = merge_accounts(datasets)

    if args.format == 'json':
        output = []
        for data in merged:
            obj = data.to_dict()
            txns = data.transactions
            if txns:
                dates = sorted(t.date for t in txns if t.date)
                if dates:
                    obj['first_transaction_date'] = str(dates[0])
                    obj['last_transaction_date'] = str(dates[-1])
            output.append(obj)
        print(json.dumps(output, indent=2, cls=DecimalEncoder))
    else:
        blocks = []
        for i, data in enumerate(merged):
            blocks.append(fmt_info_block(data, i, len(merged)))
        print("\n\n".join(blocks))


def cmd_trans(args):
    ofx_files = collect_ofx_files(args.files)
    datasets = [load_ofx(f) for f in ofx_files]
    merged = merge_accounts(datasets)

    currencies = set(d.account.currency for d in merged)
    multi_account = len(merged) > 1

    all_txns = []
    for data in merged:
        acct_number = data.account.account_number
        for t in data.transactions:
            all_txns.append((t, acct_number, data.account.currency))

    if args.sort == 'date':
        all_txns.sort(key=lambda x: x[0].date or date.min)
    elif args.sort == 'amount':
        all_txns.sort(key=lambda x: abs(x[0].amount) if x[0].amount is not None else Decimal('0'))

    if args.reverse:
        all_txns.reverse()

    if args.limit is not None:
        all_txns = all_txns[:args.limit]

    if args.format == 'json':
        output = []
        for data in merged:
            file_txns = [t for t, a, _ in all_txns if a == data.account.account_number]
            output.append({
                'files': data.source_files,
                'account': data.account.to_dict(),
                'transactions': [t.to_dict() for t in file_txns],
            })
        print(json.dumps(output, indent=2, cls=DecimalEncoder))
    elif args.format == 'csv':
        writer = csv.writer(sys.stdout)
        cols = ['fitid', 'date', 'type', 'payee', 'memo', 'amount', 'currency']
        if multi_account:
            cols.insert(1, 'account')
        writer.writerow(cols)
        for t, acct, cur in all_txns:
            row = [t.fitid, str(t.date) if t.date else '', t.type, t.payee, t.memo, t.amount, cur]
            if multi_account:
                row.insert(1, acct)
            writer.writerow(row)
    else:
        if multi_account:
            headers = ['Date', 'Account', 'Type', 'Payee', 'Amount']
            rows = [[str(t.date) if t.date else '', acct, t.type, t.payee, str(t.amount)]
                    for t, acct, _cur in all_txns]
        else:
            headers = ['Date', 'Type', 'Payee', 'Amount']
            rows = [[str(t.date) if t.date else '', t.type, t.payee, str(t.amount)]
                    for t, _acct, _cur in all_txns]
        print(format_table(headers, rows))

        total = sum((t.amount for t, _a, _c in all_txns), Decimal('0'))
        income = sum((t.amount for t, _a, _c in all_txns if t.amount > 0), Decimal('0'))
        expense = sum((t.amount for t, _a, _c in all_txns if t.amount < 0), Decimal('0'))
        curr_label = "/".join(sorted(currencies)) if len(currencies) > 1 else (currencies.pop() if currencies else "")
        print(f"\n{len(all_txns)} transactions  |  In: {income}  |  Out: {expense}  |  Net: {total}  {curr_label}")


def cmd_view(args):
    try:
        import tkinter as tk
        from tkinter import ttk
    except ImportError:
        err("tkinter is not available")

    data = load_ofx(args.file)
    acct = data.account

    root = tk.Tk()
    root.title(f"{acct.institution} - {acct.account_number}")

    info_frame = ttk.Frame(root)
    info_frame.pack(fill='x', padx=5, pady=5)
    info_text = f"{acct.start_date} to {acct.end_date}  |  Balance: {acct.ledger_balance} {acct.currency}"
    ttk.Label(info_frame, text=info_text).pack(anchor='w')

    tree = ttk.Treeview(root, columns=('Date', 'Type', 'Payee', 'Amount'), show='headings')
    tree.heading('Date', text='Date')
    tree.heading('Type', text='Type')
    tree.heading('Payee', text='Payee')
    tree.heading('Amount', text=f'Amount ({acct.currency})')
    tree.column('Date', width=100)
    tree.column('Type', width=80)
    tree.column('Payee', width=320)
    tree.column('Amount', width=100)

    for t in data.transactions:
        tree.insert('', 'end', values=(t.date, t.type, t.payee, t.amount))

    tree.pack(side='left', fill='both', expand=True)

    vsb = ttk.Scrollbar(root, orient='vertical', command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    vsb.pack(side='right', fill='y')

    root.mainloop()


def main():
    subcommands = ('info', 'trans', 'view')
    non_flags = [a for a in sys.argv[1:] if not a.startswith('-')]

    if len(sys.argv) == 1:
        argparse.ArgumentParser(
            description='OFX Toolkit - Inspect OFX financial files for reconciliation.',
        ).print_help()
        return

    if sys.argv[1] not in subcommands and sys.argv[1] not in ('-h', '--help'):
        ofx_files = collect_ofx_files(non_flags)
        datasets = [load_ofx(f) for f in ofx_files]
        merged = merge_accounts(datasets)
        for data in merged:
            acct = data.account
            n_files = len(data.source_files)
            src = f"({n_files} files) " if n_files > 1 else ""
            print(f"{acct.institution} | {acct.account_number} | {acct.start_date} to {acct.end_date} {src}")
            print(f"  Balance: {acct.ledger_balance} {acct.currency}  |  {acct.transaction_count} transactions\n")
        return

    parser = argparse.ArgumentParser(
        description='OFX Toolkit - Inspect OFX financial files for reconciliation.',
    )
    sub = parser.add_subparsers(dest='command')

    p = sub.add_parser('info', help='Display account info, date range, and balances')
    p.add_argument('files', nargs='+', help='OFX file(s) or directory(ies)')
    p.add_argument('--format', choices=['text', 'json'], default='text',
                   help='Output format: text (human) or json (agent)')

    p = sub.add_parser('trans', help='List transactions')
    p.add_argument('files', nargs='+', help='OFX file(s) or directory(ies)')
    p.add_argument('--format', choices=['table', 'json', 'csv'], default='table',
                   help='Output format: table (human), json (agent), csv')
    p.add_argument('--sort', choices=['date', 'amount'], default='date',
                   help='Sort by field')
    p.add_argument('--reverse', action='store_true', help='Reverse sort order')
    p.add_argument('--limit', type=int, metavar='N', help='Show first N transactions')

    p = sub.add_parser('view', help='Open GUI viewer (single file)')
    p.add_argument('file', help='Path to OFX file')

    args = parser.parse_args()

    if args.command == 'info':
        cmd_info(args)
    elif args.command == 'trans':
        cmd_trans(args)
    elif args.command == 'view':
        cmd_view(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

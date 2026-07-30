from ofxparse import OfxParser
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional


@dataclass
class Transaction:
    fitid: str
    type: str
    date: date
    payee: str
    memo: str
    amount: Decimal
    checknum: Optional[str] = None
    sic: Optional[str] = None
    mcc: Optional[str] = None

    def to_dict(self):
        return {
            'fitid': self.fitid,
            'type': self.type,
            'date': str(self.date),
            'payee': self.payee,
            'memo': self.memo,
            'amount': float(self.amount),
            'checknum': self.checknum or None,
            'sic': self.sic or None,
            'mcc': self.mcc or None,
        }


@dataclass
class AccountInfo:
    account_number: str
    routing_number: str
    institution: str
    institution_fid: str
    account_type: str
    branch_id: str
    currency: str
    start_date: Optional[date]
    end_date: Optional[date]
    ledger_balance: Optional[Decimal]
    available_balance: Optional[Decimal]
    transaction_count: int

    def to_dict(self):
        return {
            'account_number': self.account_number,
            'routing_number': self.routing_number,
            'institution': self.institution,
            'institution_fid': self.institution_fid,
            'account_type': self.account_type,
            'branch_id': self.branch_id,
            'currency': self.currency,
            'statement_period': {
                'start': str(self.start_date) if self.start_date else None,
                'end': str(self.end_date) if self.end_date else None,
            },
            'ledger_balance': float(self.ledger_balance) if self.ledger_balance is not None else None,
            'available_balance': float(self.available_balance) if self.available_balance is not None else None,
            'transaction_count': self.transaction_count,
        }


@dataclass
class OfxResult:
    file_path: str
    account: AccountInfo
    transactions: List[Transaction]
    source_files: List[str] = None

    def __post_init__(self):
        if self.source_files is None:
            self.source_files = [self.file_path]

    def to_dict(self):
        return {
            'files': self.source_files,
            'account': self.account.to_dict(),
            'transactions': [t.to_dict() for t in self.transactions],
        }


class OfxParserWrapper:
    def __init__(self, ofx_file):
        self.file_path = ofx_file

    def parse(self) -> OfxResult:
        with open(self.file_path, 'rb') as f:
            ofx = OfxParser.parse(f)

        acct = ofx.account
        stmt = acct.statement
        inst = acct.institution

        account_info = AccountInfo(
            account_number=getattr(acct, 'number', '') or '',
            routing_number=getattr(acct, 'routing_number', '') or '',
            institution=inst.organization if inst else '',
            institution_fid=inst.fid if inst else '',
            account_type=getattr(acct, 'account_type', '') or '',
            branch_id=getattr(acct, 'branch_id', '') or '',
            currency=stmt.currency.upper() if getattr(stmt, 'currency', None) else '',
            start_date=stmt.start_date.date() if getattr(stmt, 'start_date', None) else None,
            end_date=stmt.end_date.date() if getattr(stmt, 'end_date', None) else None,
            ledger_balance=getattr(stmt, 'balance', None),
            available_balance=getattr(stmt, 'available_balance', None),
            transaction_count=len(stmt.transactions) if getattr(stmt, 'transactions', None) else 0,
        )

        transactions = []
        for txn in (getattr(stmt, 'transactions', None) or []):
            transactions.append(Transaction(
                fitid=getattr(txn, 'id', '') or '',
                type=getattr(txn, 'type', '') or '',
                date=txn.date.date() if getattr(txn, 'date', None) else None,
                payee=getattr(txn, 'payee', '') or '',
                memo=getattr(txn, 'memo', '') or '',
                amount=getattr(txn, 'amount', None),
                checknum=getattr(txn, 'checknum', None) or None,
                sic=str(getattr(txn, 'sic', None)) if getattr(txn, 'sic', None) else None,
                mcc=getattr(txn, 'mcc', None) or None,
            ))

        return OfxResult(
            file_path=self.file_path,
            account=account_info,
            transactions=transactions,
        )

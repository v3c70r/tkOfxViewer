from ofxparse import OfxParser

class Parser:
    def __init__(self, ofx_file):
        self.fileObj = open(ofx_file, 'rb')

    def parse(self):
        ofx = OfxParser.parse(self.fileObj)
        records = [];
        for transaction in ofx.account.statement.transactions:
            records.append((transaction.date.date(), transaction.amount, transaction.payee))
        return records


if __name__ == "__main__":
    parser = Parser('./ofx/qgu-tan-ch.ofx')
    records = parser.parse()
    print(records)
#with open('./ofx/qgu-tan-ch.ofx', 'rb') as fileobj:
#    ofx = OfxParser.parse(fileobj)
#
## Access parsed data
#account = ofx.account
#for transaction in ofx.account.statement.transactions:
#    print(f"Date: {transaction.date}, Amount: {transaction.amount}, Payee: {transaction.payee}")

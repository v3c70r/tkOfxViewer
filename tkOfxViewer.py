import tkinter as tk
from tkinter import ttk
from parser import OfxParserWrapper
import argparse

parser = argparse.ArgumentParser(description="Process a file.")
parser.add_argument("file_path", help="Path to the file to be processed")
args = parser.parse_args()

file_path = args.file_path
data = OfxParserWrapper(file_path).parse()
acct = data.account

root = tk.Tk()
root.title(f"{acct.institution} - {acct.account_number}")
tree = ttk.Treeview(root, columns=("Date", "Type", "Payee", "Amount", "Currency"), show="headings")
tree.heading("Date", text="Date")
tree.heading("Type", text="Type")
tree.heading("Payee", text="Payee")
tree.heading("Amount", text="Amount")
tree.heading("Currency", text="Currency")

for t in data.transactions:
    tree.insert("", "end", values=(t.date, t.type, t.payee, t.amount, acct.currency))

tree.pack(side="left", fill="both", expand=True)

# Scrollbar
vsb = ttk.Scrollbar(root, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=vsb.set)
vsb.pack(side="right", fill="y")
root.mainloop()

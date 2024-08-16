import tkinter as tk
from tkinter import ttk
from parser import Parser
import argparse

parser = argparse.ArgumentParser(description="Process a file.")
parser.add_argument("file_path", help="Path to the file to be processed")
args = parser.parse_args()

file_path = args.file_path
root = tk.Tk()
root.title(file_path)
tree = ttk.Treeview(root, columns=("Date", "Amount", "Payee"), show="headings")
tree.heading("Date", text="Date")
tree.heading("Amount", text="Amount")
tree.heading("Payee", text="Payee")

parser = Parser(file_path)
records = parser.parse()

for record in records:
    tree.insert("", "end", values=record)

tree.pack(side="left", fill="both", expand=True)

# Scrollbar
vsb = ttk.Scrollbar(root, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=vsb.set)
vsb.pack(side="right", fill="y")
root.mainloop()

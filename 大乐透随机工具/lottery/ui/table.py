"""分页表格，保留全量数据用于导出，不把十万行一次塞进 Tk。"""
import tkinter as tk
from tkinter import ttk


class DataTable(ttk.Frame):
    PAGE_SIZE = 250

    def __init__(self, parent, columns, widths=None):
        super().__init__(parent)
        self.rows, self.page = [], 0
        self.columns = columns
        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode="extended")
        for i, col in enumerate(columns):
            self.tree.heading(col, text=col, command=lambda c=i: self.sort(c))
            self.tree.column(col, width=(widths[i] if widths else 140), minwidth=50, anchor="center")
        y = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        x = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y.set, xscrollcommand=x.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        y.grid(row=0, column=1, sticky="ns")
        x.grid(row=1, column=0, sticky="ew")
        pager = ttk.Frame(self)
        pager.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        self.previous = ttk.Button(pager, text="上一页", command=lambda: self.move(-1), width=8)
        self.previous.pack(side="left")
        self.next = ttk.Button(pager, text="下一页", command=lambda: self.move(1), width=8)
        self.next.pack(side="left", padx=5)
        self.caption = ttk.Label(pager)
        self.caption.pack(side="right")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.descending = {}
        self.tree.bind("<Control-a>", self.select_page)
        self.render()

    def select_page(self, event=None):
        self.tree.selection_set(self.tree.get_children())
        return "break"

    def set_rows(self, rows):
        self.rows, self.page = list(rows), 0
        self.render()

    def selected(self):
        return [self.rows[int(i)] for i in self.tree.selection()]

    def render(self):
        children = self.tree.get_children()
        if children:
            self.tree.delete(*children)
        start = self.page * self.PAGE_SIZE
        for index in range(start, min(start + self.PAGE_SIZE, len(self.rows))):
            self.tree.insert("", "end", iid=str(index), values=self.rows[index])
        pages = max(1, (len(self.rows) + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        self.caption.configure(text=f"{len(self.rows):,} 条 · {self.page+1}/{pages} 页")
        self.previous.configure(state="normal" if self.page else "disabled")
        self.next.configure(state="normal" if self.page + 1 < pages else "disabled")

    def move(self, offset):
        pages = max(1, (len(self.rows) + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        self.page = min(max(0, self.page + offset), pages - 1)
        self.render()

    def sort(self, column):
        reverse = not self.descending.get(column, True)
        self.descending[column] = reverse

        def key(row):
            value = row[column]
            try:
                return 0, float(str(value).rstrip("%"))
            except ValueError:
                return 1, str(value)
        self.rows.sort(key=key, reverse=reverse)
        self.page = 0
        self.render()

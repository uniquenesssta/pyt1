"""分页表格，保留全量数据用于导出，不把十万行一次塞进 Tk。"""
import tkinter as tk
from tkinter import ttk
from .theme import COLORS


class DataTable(ttk.Frame):
    PAGE_SIZE = 250

    def __init__(self, parent, columns, widths=None, empty_text="暂无记录，请先导入或更新历史数据",
                 *, edge_navigation=False):
        super().__init__(parent)
        self.rows, self.page = [], 0
        self.columns = columns
        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode="extended")
        self.tree.tag_configure('even', background=COLORS['surface'])
        self.tree.tag_configure('odd', background=COLORS['background'])
        for i, col in enumerate(columns):
            self.tree.heading(col, text=col, command=lambda c=i: self.sort(c))
            self.tree.column(col, width=(widths[i] if widths else 140), minwidth=50, anchor="center")
        y = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        x = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y.set, xscrollcommand=x.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        y.grid(row=0, column=1, sticky="ns")
        x.grid(row=1, column=0, sticky="ew")
        self.empty = ttk.Label(self.tree, text=empty_text, style="Muted.TLabel", anchor="center", justify="center")
        pager = self.pager = ttk.Frame(self)
        pager.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        self.first_page_button = self.last_page_button = None
        if edge_navigation:
            self.first_page_button = ttk.Button(pager, text="首页", command=lambda: self.go_to_page(0), width=6)
            self.last_page_button = ttk.Button(pager, text="尾页",
                                               command=lambda: self.go_to_page(self.page_count - 1), width=6)
        self.previous = ttk.Button(pager, text="上一页", command=lambda: self.move(-1), width=8)
        self.next = ttk.Button(pager, text="下一页", command=lambda: self.move(1), width=8)
        self.caption = ttk.Label(pager)
        self.caption.pack(side="right")
        self.selection_caption = ttk.Label(pager, style='Muted.TLabel')
        self.selection_caption.pack(side="left", padx=8)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.descending = {}
        self.missing_sort_values = {}
        self.tree.bind("<Control-a>", self.select_page)
        self.tree.bind("<<TreeviewSelect>>", lambda _: self.update_selection())
        self.render()

    def select_page(self, event=None):
        self.tree.selection_set(self.tree.get_children())
        return "break"

    def set_rows(self, rows):
        self.rows, self.page = list(rows), 0
        self.render()

    def selected(self):
        return [self.rows[int(i)] for i in self.tree.selection()]

    @property
    def page_count(self):
        return max(1, (len(self.rows) + self.PAGE_SIZE - 1) // self.PAGE_SIZE)

    def render(self):
        children = self.tree.get_children()
        if children:
            self.tree.delete(*children)
        start = self.page * self.PAGE_SIZE
        for index in range(start, min(start + self.PAGE_SIZE, len(self.rows))):
            self.tree.insert("", "end", iid=str(index), values=self.rows[index], tags=('odd' if index % 2 else 'even',))
        pages = self.page_count
        self.caption.configure(text=f"{len(self.rows):,} 条 · {self.page+1}/{pages} 页")
        can_go_back = self.page > 0
        can_go_forward = self.page + 1 < pages
        for button, available in ((self.first_page_button, can_go_back), (self.previous, can_go_back),
                                  (self.next, can_go_forward), (self.last_page_button, can_go_forward)):
            if button is None:
                continue
            button.configure(state="normal" if available else "disabled")
            if self.first_page_button is not None or pages > 1:
                button.pack(side="left", padx=(0, 5), before=self.selection_caption)
            else:
                button.pack_forget()
        if self.rows:
            self.empty.place_forget()
        else:
            self.empty.place(relx=.5, rely=.5, anchor='center')
        self.update_selection()

    def update_selection(self):
        count = len(self.tree.selection())
        self.selection_caption.configure(text=f'已选 {count} 条' if count else 'Ctrl / Shift 多选')

    def move(self, offset):
        self.go_to_page(self.page + offset)

    def go_to_page(self, index):
        page = min(max(0, index), self.page_count - 1)
        if page != self.page:
            self.page = page
            self.render()
            self.tree.yview_moveto(0)

    def sort(self, column):
        reverse = not self.descending.get(column, True)

        def key(row):
            value = row[column]
            try:
                return 0, float(str(value).lstrip("≥").rstrip("%"))
            except ValueError:
                return 1, str(value)
        self.rows.sort(key=key, reverse=reverse)
        if column in self.missing_sort_values:
            missing = self.missing_sort_values[column]
            self.rows.sort(key=lambda row: row[column] == missing)
        self.mark_sort(column, reverse)
        self.page = 0
        self.render()

    def mark_sort(self, column, reverse):
        self.descending[column] = reverse
        for i, col in enumerate(self.columns):
            self.tree.heading(col, text=col + ((' ▼' if reverse else ' ▲') if i == column else ''))

    def bind_open(self, callback):
        def open_row(event):
            if self.tree.identify_region(event.x, event.y) not in ('cell', 'tree'):
                return
            item = self.tree.identify_row(event.y)
            if item:
                callback(self.rows[int(item)])
        self.tree.bind('<Double-1>', open_row)

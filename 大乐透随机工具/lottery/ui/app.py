"""窗口组装和任务协调，算法、文件操作与页面各自独立。"""
import logging
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ..core.generation import generate
from ..core.querying import search
from ..core.statistics import analyze
from ..data.importing import load_dataset
from ..data.storage import FavoriteStore
from .controls import GenerationControls
from .history import HistoryPage
from .import_issues import show_import_issues
from .jobs import Jobs
from .results import TicketPanel
from .statistics import StatisticsPage


class LotteryApp:
    def __init__(self, root, data_dir):
        self.root = root
        self.dataset, self.stats = None, None
        self.store = FavoriteStore(Path(data_dir) / "favorites.json")
        self.favorites = self.store.load()
        root.title("大乐透随机工具")
        root.geometry("1180x780")
        root.minsize(960, 640)
        style = ttk.Style(root)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        else:
            style.theme_use("clam")
        root.option_add("*Font", "{Microsoft YaHei UI} 10")
        style.configure("Treeview", rowheight=30, font=("Microsoft YaHei UI", 10))
        style.configure("Treeview.Heading", font=("Microsoft YaHei UI", 10, "bold"))
        style.configure("Section.TLabel", font=("Microsoft YaHei UI", 12, "bold"))
        style.configure("Muted.TLabel", foreground="#64748b")
        style.configure("Primary.TButton", font=("Microsoft YaHei UI", 11, "bold"), padding=(15, 6))
        outer = ttk.Frame(root, padding=12)
        outer.pack(fill="both", expand=True)
        header = ttk.Frame(outer)
        header.pack(fill="x", pady=(0, 10))
        ttk.Label(header, text="大乐透随机工具", style="Section.TLabel").pack(side="left")
        self.import_button = ttk.Button(header, text="导入历史 TXT / CSV / Excel", command=self.import_file)
        self.import_button.pack(side="right")
        self.issue_button = ttk.Button(header, text="校验明细", command=self.show_issues)
        self.issue_button.pack(side="right", padx=8)
        self.source_text = tk.StringVar(value="尚未导入历史数据 · 可直接随机")
        ttk.Label(outer, textvariable=self.source_text, style="Muted.TLabel", wraplength=1100).pack(fill="x", pady=(0, 10))
        self.tabs = ttk.Notebook(outer)
        self.tabs.pack(fill="both", expand=True)
        generation = ttk.Frame(self.tabs, padding=8)
        self.tabs.add(generation, text="  随机选号  ")
        self.controls = GenerationControls(generation, self.generate)
        self.controls.pack(fill="x")
        panels = ttk.PanedWindow(generation, orient="horizontal")
        panels.pack(fill="both", expand=True)
        self.generated = TicketPanel(panels, "本批号码", self.set_status, self.error, self.add_favorites, "收藏选中")
        self.saved = TicketPanel(panels, "我的收藏", self.set_status, self.error, self.remove_favorites, "移除选中")
        panels.add(self.generated, weight=1)
        panels.add(self.saved, weight=1)
        self.saved.set_tickets(self.favorites)
        self.history = HistoryPage(self.tabs, self.search, self.set_status, self.error)
        self.statistics = StatisticsPage(self.tabs, self.set_status, self.error)
        self.tabs.add(self.history, text="  历史查询  ")
        self.tabs.add(self.statistics, text="  统计分析  ")
        footer = ttk.Frame(outer)
        footer.pack(fill="x", pady=(10, 0))
        self.status = tk.StringVar(value="就绪")
        ttk.Label(footer, textvariable=self.status, wraplength=980).pack(side="left", fill="x", expand=True)
        self.cancel_button = ttk.Button(footer, text="取消任务", command=lambda: self.jobs.cancel.set(), state="disabled")
        self.cancel_button.pack(side="right")
        self.jobs = Jobs(root, self.set_status, self.set_busy)
        root.protocol("WM_DELETE_WINDOW", self.close)

    def set_status(self, text):
        self.status.set(text)

    def set_busy(self, busy):
        for button in (self.import_button, self.controls.generate_button, self.history.search_button):
            button.configure(state="disabled" if busy else "normal")
        self.cancel_button.configure(state="normal" if busy else "disabled")

    def error(self, error, detail=None):
        logging.error("%s\n%s", error, detail or "")
        self.set_status(str(error).splitlines()[0])
        messagebox.showerror("操作未完成", str(error), parent=self.root)

    def generate(self):
        try:
            config = self.controls.snapshot()
        except ValueError as error:
            self.error(error)
            return
        stats = self.stats

        def done(tickets):
            self.generated.set_tickets(tickets)
            self.set_status(f"已生成 {len(tickets):,} 组 · {config.mode}")
        self.set_status("正在生成…")
        self.jobs.start(lambda cancel, progress: generate(config, stats, cancel, progress), done, self.error)

    def import_file(self):
        path = filedialog.askopenfilename(parent=self.root, filetypes=[("历史数据", "*.txt *.csv *.tsv *.xls *.xlsx *.xlxs"), ("Excel 工作簿", "*.xls *.xlsx *.xlxs"), ("所有文件", "*.*")])
        if path:
            self.load_path(path)

    def load_path(self, path):
        def work(cancel, progress):
            dataset = load_dataset(path, cancel, progress)
            progress(f"正在分析 {len(dataset.draws):,} 条有效记录")
            return dataset, analyze(dataset.draws, cancel)

        def done(value):
            self.dataset, self.stats = value
            d = self.dataset
            self.source_text.set(f"{Path(d.source).name} · 有效 {len(d.draws):,} 行 · 无效 {len(d.issues):,} 行 · 重复 {d.duplicates:,} 行 · {d.encoding}")
            self.history.text.set("")
            self.history.set_results([(draw, "") for draw in d.draws], len(d.draws))
            self.statistics.set_statistics(self.stats)
            self.set_status("导入完成，选号加权、历史查询和全部统计共用本次数据")
        self.set_status("正在读取文件…")
        self.jobs.start(work, done, self.error)

    def search(self):
        if self.dataset is None:
            self.set_status("请先导入历史数据")
            return
        query, draws = self.history.snapshot(), self.dataset.draws
        self.jobs.start(lambda cancel, progress: search(draws, query, cancel),
                        lambda rows: (self.history.set_results(rows, len(draws)), self.set_status(f"查询完成，匹配 {len(rows):,} 条")), self.error)

    def show_issues(self):
        if self.dataset is None:
            self.set_status("请先导入历史数据")
            return
        show_import_issues(self.root, self.dataset, self.error)

    def commit_favorites(self, tickets):
        try:
            self.store.save(tickets)
        except OSError as error:
            self.error(error)
            return False
        self.favorites = tickets
        self.saved.set_tickets(tickets)
        return True

    def add_favorites(self, tickets):
        if not tickets:
            self.set_status("请先选择要收藏的号码")
            return
        updated = list(dict.fromkeys(self.favorites + tickets))
        added = len(updated) - len(self.favorites)
        if self.commit_favorites(updated):
            self.set_status(f"新增收藏 {added} 组，已自动保存")

    def remove_favorites(self, tickets):
        if not tickets:
            self.set_status("请先选择要移除的收藏")
            return
        removed = set(tickets)
        if self.commit_favorites([t for t in self.favorites if t not in removed]):
            self.set_status(f"已移除 {len(removed)} 组收藏")

    def close(self):
        self.jobs.close()
        self.root.destroy()

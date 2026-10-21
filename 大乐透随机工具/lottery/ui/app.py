"""窗口组装和任务协调，算法、文件操作与页面各自独立。"""
import logging
from dataclasses import replace
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ..core.generation import generate, MODES
from ..core.querying import search
from ..data.history_store import HistoryStore
from .history_actions import import_history, update_history, restore_history
from ..data.storage import FavoriteStore
from .controls import GenerationControls
from .history import HistoryPage
from .import_issues import show_import_issues
from .jobs import Jobs
from .results import TicketPanel
from .statistics import StatisticsPage
from .structure_weights import StructureWeightsPage


class LotteryApp:
    def __init__(self, root, data_dir):
        self.root = root
        self.dataset, self.stats = None, None
        self.history_store = HistoryStore(Path(data_dir) / "history.json")
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
        self.update_button = ttk.Button(header, text="更新开奖数据", command=lambda: update_history(self))
        self.update_button.pack(side="right", padx=8)
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
        self.structure_weights = StructureWeightsPage(self.tabs, self.error)
        self.tabs.add(self.structure_weights, text="  结构权重  ")
        footer = ttk.Frame(outer)
        footer.pack(fill="x", pady=(10, 0))
        self.status = tk.StringVar(value="就绪")
        ttk.Label(footer, textvariable=self.status, wraplength=980).pack(side="left", fill="x", expand=True)
        self.cancel_button = ttk.Button(footer, text="取消任务", command=lambda: self.jobs.cancel.set(), state="disabled")
        self.cancel_button.pack(side="right")
        self.jobs = Jobs(root, self.set_status, self.set_busy)
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.restore_timer = root.after(100, lambda: restore_history(self))

    def set_status(self, text):
        self.status.set(text)

    def set_busy(self, busy):
        self.structure_weights.set_busy(busy)
        for button in (self.import_button, self.update_button, self.controls.generate_button, self.history.search_button):
            button.configure(state="disabled" if busy else "normal")
        self.cancel_button.configure(state="normal" if busy else "disabled")

    def error(self, error, detail=None):
        logging.error("%s\n%s", error, detail or "")
        self.set_status(str(error).splitlines()[0])
        messagebox.showerror("操作未完成", str(error), parent=self.root)

    def generate(self):
        try:
            config = self.controls.snapshot()
            if config.mode != MODES[0]:
                config = replace(config, structure_profile=self.structure_weights.snapshot())
        except ValueError as error:
            self.error(error)
            return
        stats = self.stats

        def done(tickets):
            self.generated.set_tickets(tickets)
            self.set_status(f"已生成 {len(tickets):,} 组 · {config.mode}" + (f" · 实际使用最近 {len(config.structure_profile.draws)} 期" if config.structure_profile else ""))
        self.set_status("正在生成…")
        self.jobs.start(lambda cancel, progress: generate(config, stats, cancel, progress), done, self.error)

    def import_file(self):
        path = filedialog.askopenfilename(parent=self.root, filetypes=[("历史数据", "*.txt *.csv *.tsv *.xls *.xlsx *.xlxs"), ("Excel 工作簿", "*.xls *.xlsx *.xlxs"), ("所有文件", "*.*")])
        if path:
            self.load_path(path)

    def load_path(self, path):
        import_history(self, path)

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
        self.root.after_cancel(self.restore_timer)
        self.jobs.close()
        self.root.destroy()

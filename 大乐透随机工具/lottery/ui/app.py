"""窗口组装和任务协调，算法、文件操作与页面各自独立。"""
import logging
from dataclasses import replace
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ..core.generation import generate, MODES
from ..core.structure_cache import StructureCache
from ..data.history_store import HistoryStore
from .history_actions import import_history, update_history, restore_history
from ..data.storage import FavoriteStore
from .controls import GenerationControls
from .history import HistoryPage
from .history_navigation import search_history, open_statistic
from .import_issues import show_import_issues
from .jobs import Jobs
from .results import TicketPanel
from .statistics import StatisticsPage
from .structure_weights import StructureWeightsPage
from .cross_link import CrossWeightLink
from .theme import apply_theme
from .widgets import wrapped_label, FormViewport


class LotteryApp:
    def __init__(self, root, data_dir):
        self.root = root
        self.dataset, self.stats = None, None
        self.structure_cache = StructureCache()
        self.history_store = HistoryStore(Path(data_dir) / "history.json")
        self.store = FavoriteStore(Path(data_dir) / "favorites.json")
        self.favorites = self.store.load()
        root.title("大乐透随机工具")
        root.geometry("1240x840")
        root.minsize(1040, 740)
        apply_theme(root)
        outer = ttk.Frame(root, padding=20, style="Workspace.TFrame")
        outer.pack(fill="both", expand=True)
        header = ttk.Frame(outer, style="Workspace.TFrame")
        header.pack(fill="x", pady=(0, 10))
        ttk.Label(header, text="大乐透随机工具", style="Title.TLabel").pack(side="left")
        self.update_button = ttk.Button(header, text="更新开奖数据", command=lambda: update_history(self), style="Primary.TButton")
        self.update_button.pack(side="right")
        self.import_button = ttk.Button(header, text="导入历史", command=self.import_file)
        self.import_button.pack(side="right", padx=8)
        self.issue_button = ttk.Button(header, text="校验明细", command=self.show_issues)
        self.issue_button.pack(side="right", padx=8)
        self.source_text = tk.StringVar(value="尚未导入历史数据 · 可直接随机")
        wrapped_label(outer, textvariable=self.source_text, style="Workspace.TLabel").pack(fill="x", pady=(0, 16))
        self.tabs = ttk.Notebook(outer)
        self.tabs.pack(fill="both", expand=True)
        generation = self.generation = ttk.Frame(self.tabs, style="Workspace.TFrame")
        self.tabs.add(generation, text="  随机选号  ")
        self.form_viewport = FormViewport(generation)
        self.form_viewport.pack(fill="x", pady=(0, 12))
        self.controls = GenerationControls(self.form_viewport.body, self.generate)
        self.controls.pack(fill="x")
        self.form_viewport.bind_controls()
        self.results_tabs = ttk.Notebook(generation)
        self.results_tabs.pack(fill="both", expand=True)
        self.generated = TicketPanel(self.results_tabs, "本批号码", self.set_status, self.error, self.add_favorites, "收藏选中")
        self.saved = TicketPanel(self.results_tabs, "我的收藏", self.set_status, self.error, self.remove_favorites, "移除选中")
        self.results_tabs.add(self.generated, text="本批号码")
        self.results_tabs.add(self.saved, text=f"我的收藏 ({len(self.favorites)})")
        self.saved.set_tickets(self.favorites)
        self.history = HistoryPage(self.tabs, self.search, self.set_status, self.error)
        self.statistics = StatisticsPage(self.tabs, self.set_status, self.error)
        self.tabs.add(self.history, text="  历史查询  ")
        self.tabs.add(self.statistics, text="  统计分析  ")
        self.structure_weights = StructureWeightsPage(self.tabs, self.error)
        self.tabs.add(self.structure_weights, text="  结构权重  ")
        self.controls.on_structure = lambda: self.tabs.select(self.structure_weights)
        self.structure_weights.on_generate = lambda: self.tabs.select(self.generation)
        self.history.on_return = lambda: self.tabs.select(self.structure_weights if self.history.statistic and self.history.statistic.source == "结构权重" else self.statistics)
        self.statistics.hot_cold.on_open = lambda area, number, periods: open_statistic(self, "统计分析", area+"·期数占比", number, periods_override=periods)
        self.statistics.table.bind_open(lambda row: open_statistic(self, "统计分析", row[0], row[1], periods_override=self.statistics.active_periods))
        self.structure_weights.table.bind_open(lambda row: open_statistic(self, "结构权重", self.structure_weights.group.get(), row[0]))
        self.cross_link = CrossWeightLink(self.controls, self.structure_weights, self.error)
        footer = ttk.Frame(outer, style="Workspace.TFrame")
        footer.pack(fill="x", pady=(10, 0))
        self.status = tk.StringVar(value="就绪")
        wrapped_label(footer, textvariable=self.status, style="Workspace.TLabel").pack(side="left", fill="x", expand=True)
        self.cancel_button = ttk.Button(footer, text="取消任务", command=lambda: self.jobs.cancel.set(), state="disabled")
        self.cancel_button.pack(side="right")
        self.jobs = Jobs(root, self.set_status, self.set_busy)
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.restore_timer = root.after(100, lambda: restore_history(self))

    def set_status(self, text):
        self.status.set(text)

    def set_busy(self, busy):
        self.structure_weights.set_busy(busy)
        self.statistics.set_busy(busy)
        for button in (self.import_button, self.update_button, self.controls.generate_button, self.controls.fill_button, self.controls.cross_period_box, self.history.search_button, self.history.period_box, self.history.clear_button, self.history.reset_button, self.history.back_button):
            button.configure(state="disabled" if busy else "normal")
        if not busy:
            self.history.update_condition_buttons()
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
        cache_hits_before = self.structure_cache.hits

        def done(tickets):
            self.generated.set_tickets(tickets)
            self.results_tabs.tab(self.generated, text=f"本批号码 ({len(tickets)})")
            self.results_tabs.select(self.generated)
            self.set_status(f"已生成 {len(tickets):,} 组 · {config.mode}" + (f" · 实际使用最近 {len(config.structure_profile.draws)} 期" if config.structure_profile else "") + (" · 已复用候选缓存" if self.structure_cache.hits > cache_hits_before else ""))
        self.set_status("正在生成…")
        self.jobs.start(lambda cancel, progress: generate(config, stats, cancel, progress, structure_cache=self.structure_cache), done, self.error)

    def import_file(self):
        path = filedialog.askopenfilename(parent=self.root, filetypes=[("历史数据", "*.txt *.csv *.tsv *.xls *.xlsx *.xlxs"), ("Excel 工作簿", "*.xls *.xlsx *.xlxs"), ("所有文件", "*.*")])
        if path:
            self.load_path(path)

    def load_path(self, path):
        import_history(self, path)

    def search(self):
        search_history(self)

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
        self.results_tabs.tab(self.saved, text=f"我的收藏 ({len(tickets)})")
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
        self.structure_cache.clear()
        self.root.destroy()

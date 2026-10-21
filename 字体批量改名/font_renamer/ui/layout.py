import tkinter as tk
from tkinter import ttk

class LayoutMixin:
    def _create_widgets(self) -> None:
        root = ttk.Frame(self, padding=10)
        root.pack(fill=tk.BOTH, expand=True)

        # 文件夹选择
        folder_frame = ttk.LabelFrame(root, text="1. 选择字体文件夹", padding=10)
        folder_frame.pack(fill=tk.X)
        folder_frame.columnconfigure(1, weight=1)

        ttk.Label(folder_frame, text="文件夹：").grid(row=0, column=0, sticky="w")
        ttk.Entry(folder_frame, textvariable=self.folder_var).grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Button(folder_frame, text="浏览...", command=self.choose_folder).grid(row=0, column=2)

        # 选项
        option_frame = ttk.LabelFrame(root, text="2. 改名规则", padding=10)
        option_frame.pack(fill=tk.X, pady=(10, 0))

        ext_frame = ttk.Frame(option_frame)
        ext_frame.grid(row=0, column=0, columnspan=6, sticky="w", pady=(0, 6))
        ttk.Label(ext_frame, text="处理格式：").pack(side=tk.LEFT)
        for ext, var in self.ext_vars.items():
            ttk.Checkbutton(ext_frame, text=ext, variable=var).pack(side=tk.LEFT, padx=(6, 0))

        ttk.Label(option_frame, text="NameID 优先级：").grid(row=1, column=0, sticky="w")
        ttk.Entry(option_frame, textvariable=self.name_ids_var, width=18).grid(row=1, column=1, sticky="w", padx=(0, 14))

        ttk.Label(option_frame, text="语言优先级：").grid(row=1, column=2, sticky="w")
        ttk.Entry(option_frame, textvariable=self.lang_ids_var, width=34).grid(row=1, column=3, sticky="w", padx=(0, 14))

        ttk.Label(option_frame, text="重名处理：").grid(row=1, column=4, sticky="w")
        ttk.Combobox(
            option_frame,
            textvariable=self.duplicate_var,
            values=("自动添加数字后缀", "跳过重名文件"),
            width=18,
            state="readonly",
        ).grid(row=1, column=5, sticky="w")

        ttk.Checkbutton(option_frame, text="包含子文件夹", variable=self.recursive_var).grid(row=2, column=0, sticky="w", pady=(6, 0))
        ttk.Checkbutton(option_frame, text="扩展名统一小写", variable=self.lower_ext_var).grid(row=2, column=1, sticky="w", pady=(6, 0))
        ttk.Checkbutton(option_frame, text="空格替换为下划线", variable=self.underscore_var).grid(row=2, column=2, sticky="w", pady=(6, 0))

        help_text = "默认优先读取中文名称：0x0804 简中，0x0404 繁中台湾，0x0C04 繁中香港，0x0409 英文，0 Mac。"
        ttk.Label(option_frame, text=help_text).grid(row=3, column=0, columnspan=6, sticky="w", pady=(8, 0))

        # 操作按钮
        action_frame = ttk.Frame(root)
        action_frame.pack(fill=tk.X, pady=(10, 0))

        self.scan_btn = ttk.Button(action_frame, text="扫描并预览", command=self.scan_preview)
        self.scan_btn.pack(side=tk.LEFT)
        self.rename_btn = ttk.Button(action_frame, text="执行改名", command=self.rename_files, state=tk.DISABLED)
        self.rename_btn.pack(side=tk.LEFT, padx=(8, 0))
        self.export_btn = ttk.Button(action_frame, text="导出预览 CSV", command=self.export_preview, state=tk.DISABLED)
        self.export_btn.pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(action_frame, text="清空结果", command=self.clear_results).pack(side=tk.LEFT, padx=(8, 0))

        ttk.Button(action_frame, text="重复字体清理", command=self.open_duplicates).pack(side=tk.LEFT, padx=(8, 0))

        ttk.Button(action_frame, text="同名字体对比", command=self.open_same_names).pack(side=tk.LEFT, padx=(8, 0))

        self.progress = ttk.Progressbar(action_frame, mode="indeterminate", length=220)
        self.progress.pack(side=tk.RIGHT)

        # 预览表格
        preview_frame = ttk.LabelFrame(root, text="3. 预览结果", padding=8)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        preview_frame.rowconfigure(1, weight=1)
        preview_frame.columnconfigure(0, weight=1)

        filter_bar = ttk.Frame(preview_frame)
        filter_bar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        ttk.Label(filter_bar, text="状态：").pack(side=tk.LEFT)
        self.preview_filter = ttk.Combobox(
            filter_bar, textvariable=self.preview_filter_var,
            values=("全部", "跳过", "将重命名", "错误"), state="readonly", width=12,
        )
        self.preview_filter.pack(side=tk.LEFT)
        self.preview_filter.bind("<<ComboboxSelected>>", self._on_preview_filter_changed)
        ttk.Label(filter_bar, textvariable=self.preview_count_var).pack(side=tk.RIGHT)

        columns = ("status", "old", "new", "font", "name_id", "lang", "reason")
        self.tree = ttk.Treeview(preview_frame, columns=columns, show="headings", height=12)
        self.tree.heading("status", text="状态")
        self.tree.heading("old", text="原文件名")
        self.tree.heading("new", text="新文件名")
        self.tree.heading("font", text="读取到的字体名")
        self.tree.heading("name_id", text="NameID")
        self.tree.heading("lang", text="LangID")
        self.tree.heading("reason", text="说明")

        self.tree.column("status", width=82, anchor="center")
        self.tree.column("old", width=210)
        self.tree.column("new", width=230)
        self.tree.column("font", width=220)
        self.tree.column("name_id", width=70, anchor="center")
        self.tree.column("lang", width=90, anchor="center")
        self.tree.column("reason", width=260)

        ybar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.tree.yview)
        xbar = ttk.Scrollbar(preview_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)
        self.tree.grid(row=1, column=0, sticky="nsew")
        ybar.grid(row=1, column=1, sticky="ns")
        xbar.grid(row=2, column=0, sticky="ew")

        # 日志
        log_frame = ttk.LabelFrame(root, text="日志", padding=8)
        log_frame.pack(fill=tk.BOTH, expand=False, pady=(10, 0))
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)

        self.log_text = tk.Text(log_frame, height=7, wrap="word")
        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        log_scroll.grid(row=0, column=1, sticky="ns")


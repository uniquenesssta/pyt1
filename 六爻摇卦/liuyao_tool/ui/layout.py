"""本卦、之卦及说明的界面布局。"""
import tkinter as tk
from tkinter import font as tk_font
from tkinter import ttk

from ..domain.yao import YAO_NAMES


def build_layout(view):
    root = view.master
    body = tk.Frame(root, bg="#f0f0f0")
    body.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)
    fonts = {
        "normal": tk_font.Font(root=root, family="微软雅黑", size=10),
        "header": tk_font.Font(root=root, family="微软雅黑", size=12, weight="bold"),
        "small": tk_font.Font(root=root, family="微软雅黑", size=9),
        "symbol": tk_font.Font(root=root, family="Courier New", size=18, weight="bold"),
    }
    # 保留字体引用，避免离开布局函数后被 Tk 删除。
    view.fonts = fonts
    tk.Label(
        body,
        text="模拟三枚铜钱起卦，生成本卦与之卦。爻位从下方初爻到上方上爻排列。",
        font=fonts["normal"], bg="#e9e9e9", anchor="w", padx=10, pady=10,
        wraplength=660, justify=tk.LEFT,
    ).pack(fill=tk.X, pady=(0, 10))

    hexagrams = tk.Frame(body, bg="#f0f0f0")
    hexagrams.pack(fill=tk.X)
    hexagrams.columnconfigure(0, weight=1, uniform="hexagram")
    hexagrams.columnconfigure(1, weight=1, uniform="hexagram")
    _build_hexagram(view, hexagrams, fonts, original=True)
    _build_hexagram(view, hexagrams, fonts, original=False)

    view.start_button = tk.Button(
        body, text="开始摇卦", font=("微软雅黑", 14, "bold"),
        bg="#4caf50", fg="white", relief=tk.RAISED, borderwidth=2,
        padx=25, pady=8,
    )
    view.start_button.pack(pady=(12, 10))
    ttk.Separator(body, orient="horizontal").pack(fill=tk.X, pady=(0, 8))
    _build_instructions(body, fonts)


def _build_hexagram(view, parent, fonts, original):
    background = "#e0e0e0" if original else "#d0d0d0"
    panel = tk.Frame(parent, bg=background, relief=tk.SUNKEN, borderwidth=2)
    panel.grid(row=0, column=0 if original else 1, sticky="nsew", padx=4)
    header = tk.Frame(panel, bg=background)
    header.pack(fill=tk.X, padx=8, pady=(8, 3))
    header.columnconfigure(0, weight=1)
    title = {"text": "本卦（初始状态）"} if original else {"textvariable": view.changed_title}
    tk.Label(header, **title, font=fonts["header"], bg=background).grid(row=0, column=0)
    copy_button = tk.Button(
        header, text="复制本卦" if original else "复制之卦",
        command=view.copy_original if original else view.copy_changed,
        state=tk.DISABLED, font=fonts["small"], width=8, padx=3, pady=2,
        relief=tk.GROOVE, borderwidth=1,
    )
    copy_button.grid(row=0, column=1, padx=(6, 0))
    if original:
        view.original_copy_button = copy_button
    else:
        view.changed_copy_button = copy_button
    explanation = (
        "本卦是直接摇得的卦象，显示初始状态；O、X 标记动爻。"
        if original else "之卦由动爻阴阳反转而来；静爻保持不变。"
    )
    tk.Label(panel, text=explanation, wraplength=265, height=2, font=fonts["small"],
             bg=background, fg="#444", justify=tk.LEFT).pack(padx=8, pady=(0, 8))
    for index in range(5, -1, -1):
        row = tk.Frame(panel, bg=background)
        row.pack(fill=tk.X, padx=8, pady=4)
        tk.Label(row, text=YAO_NAMES[index], width=4, anchor="w",
                 font=fonts["normal"], bg=background).pack(side=tk.LEFT)
        symbols = view.original_symbols if original else view.changed_symbols
        tk.Label(row, textvariable=symbols[index], width=7, font=fonts["symbol"],
                 relief=tk.GROOVE, borderwidth=1, bg="white",
                 fg="#00008b" if original else "#8b0000").pack(side=tk.LEFT, padx=(4, 6))
        if original:
            tk.Label(row, textvariable=view.original_names[index], anchor="w",
                     font=fonts["small"], bg=background, fg="#444").pack(side=tk.LEFT)


def _build_instructions(parent, fonts):
    # 说明可滚动，小屏幕仍保留上方卦象和操作按钮。
    area = tk.Frame(parent, bg="#f0f0f0")
    area.pack(fill=tk.BOTH, expand=True)
    canvas = tk.Canvas(area, bg="#f0f0f0", highlightthickness=0, height=260)
    scrollbar = ttk.Scrollbar(area, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    content = tk.Frame(canvas, bg="#f0f0f0")
    item = canvas.create_window(0, 0, window=content, anchor="nw")
    wrapped = []

    def add_label(text, header=False):
        label = tk.Label(
            content, text=text, anchor="w", justify=tk.LEFT, bg="#f0f0f0",
            font=fonts["header"] if header else fonts["small"],
        )
        label.pack(fill=tk.X, anchor="w", pady=(6, 4) if header else (1, 4))
        wrapped.append(label)

    add_label("爻象符号说明", header=True)
    for text in (
        "—————  少阳（7）：静爻，本卦为阳，之卦仍为阳。",
        "—   —  少阴（8）：静爻，本卦为阴，之卦仍为阴。",
        "— O —  老阳（9）：动爻，本卦为阳，之卦变为阴。",
        "— X —  老阴（6）：动爻，本卦为阴，之卦变为阳。",
    ):
        add_label(text)
    ttk.Separator(content, orient="horizontal").pack(fill=tk.X, pady=8)
    add_label("摇卦流程", header=True)
    add_label(
        "1. 点击“开始摇卦”，六个爻位开始摇动，并陆续停止。\n"
        "2. 左侧显示本卦及少阳、少阴、老阳、老阴；右侧自动生成之卦。\n"
        "3. 无动爻时，本卦与之卦相同；有动爻时，仅相应爻位阴阳反转。\n"
        "4. 一轮结束后可再次点击，重新独立起卦。"
    )

    def resize(event):
        canvas.itemconfigure(item, width=event.width)
        for label in wrapped:
            label.configure(wraplength=max(100, event.width - 12))

    def scroll(event):
        direction = -1 if event.num == 4 or event.delta > 0 else 1
        canvas.yview_scroll(direction, "units")
        return "break"

    def bind_scroll(widget):
        widget.bind("<MouseWheel>", scroll)
        widget.bind("<Button-4>", scroll)
        widget.bind("<Button-5>", scroll)
        for child in widget.winfo_children():
            bind_scroll(child)

    canvas.bind("<Configure>", resize)
    content.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox("all")))
    bind_scroll(canvas)
    bind_scroll(content)

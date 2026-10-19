"""可滚动的起卦使用说明。"""
import tkinter as tk
from tkinter import ttk


def build_instructions(parent, fonts):
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

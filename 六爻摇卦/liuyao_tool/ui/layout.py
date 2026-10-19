"""本卦、之卦及说明的界面布局。"""
import tkinter as tk
from tkinter import font as tk_font
from tkinter import ttk

from .hexagram_panel import build_hexagram
from .reading_panel import ReadingPanel


def build_layout(view):
    root = view.master
    body = tk.Frame(root, bg="#f0f0f0")
    body.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)
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
        text="爻位自下而上排列，O、X 为动爻。起卦后可查看两卦原文与参考解读。",
        font=fonts["small"], bg="#e9e9e9", anchor="w", padx=10, pady=4,
        wraplength=660, justify=tk.LEFT,
    ).pack(fill=tk.X, pady=(0, 6))

    hexagrams = tk.Frame(body, bg="#f0f0f0")
    hexagrams.pack(fill=tk.X)
    hexagrams.columnconfigure(0, weight=1, uniform="hexagram")
    hexagrams.columnconfigure(1, weight=1, uniform="hexagram")
    build_hexagram(view, hexagrams, fonts, original=True)
    build_hexagram(view, hexagrams, fonts, original=False)

    view.start_button = tk.Button(
        body, text="开始摇卦", font=("微软雅黑", 14, "bold"),
        bg="#4caf50", fg="white", relief=tk.RAISED, borderwidth=2,
        padx=25, pady=5,
    )
    view.start_button.pack(pady=(8, 6))
    ttk.Separator(body, orient="horizontal").pack(fill=tk.X, pady=(0, 8))
    view.reading_panel = ReadingPanel(body, fonts)

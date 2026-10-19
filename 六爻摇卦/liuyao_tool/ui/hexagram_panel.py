"""本卦和之卦的独立显示面板。"""
import tkinter as tk

from ..domain.yao import YAO_NAMES


def build_hexagram(view, parent, fonts, original):
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
    name = view.original_hex_name if original else view.changed_hex_name
    tk.Label(panel, textvariable=name, height=1, font=fonts["normal"],
             bg=background, fg="#333").pack(pady=(0, 4))
    for index in range(5, -1, -1):
        row = tk.Frame(panel, bg=background)
        row.pack(fill=tk.X, padx=8, pady=2)
        tk.Label(row, text=YAO_NAMES[index], width=4, anchor="w",
                 font=fonts["normal"], bg=background).pack(side=tk.LEFT)
        symbols = view.original_symbols if original else view.changed_symbols
        tk.Label(row, textvariable=symbols[index], width=7, font=fonts["symbol"],
                 relief=tk.GROOVE, borderwidth=1, bg="white",
                 fg="#00008b" if original else "#8b0000").pack(side=tk.LEFT, padx=(4, 6))
        if original:
            tk.Label(row, textvariable=view.original_names[index], anchor="w",
                     font=fonts["small"], bg=background, fg="#444").pack(side=tk.LEFT)

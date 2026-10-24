"""Visible custom-size action shared by every scene."""
from tkinter import ttk, simpledialog
from scene_tool.config.product_size import PRODUCT_SIZE_CHOICES, normalize_size


def product_size_row(results, variable):
    variable.set(normalize_size(variable.get()))
    label = results.result('产品尺寸', variable, None, choices=PRODUCT_SIZE_CHOICES)
    label.configure(width=10)
    def edit():
        value = simpledialog.askstring('自己填尺寸', '填写产品实际宽度和高度（请带单位）\n例如：宽2米 × 高1.5米；多块产品可分别说明。',
                                      initialvalue=variable.get(), parent=results)
        if value and value.strip():
            variable.set(value.strip())
    button = ttk.Button(label.master, text='自己填尺寸', width=10, command=edit)
    button.pack(side='right', before=label.editor, padx=(2, 4))
    return label

"""Aligned flag columns; spacing belongs to cells, not checkbox text."""
from tkinter import ttk, font


def flag_cell(parent, style=None):
    size = font.nametofont('TkDefaultFont')
    cell = ttk.Frame(parent, width=size.measure('隐藏') + 18,
                     height=size.metrics('linespace') + 6, **({'style': style} if style else {}))
    cell.pack(side='right', fill='y')
    cell.pack_propagate(False)
    return cell


def flag_heading(parent, text):
    ttk.Label(flag_cell(parent), text=text).place(relx=.5, rely=.5, anchor='center')


def flag_control(parent, variable, command=None):
    cell = flag_cell(parent, 'Result.TFrame')
    control = ttk.Checkbutton(cell, variable=variable, command=command,
                              width=0, style='Result.TCheckbutton')
    control.place(relx=.5, rely=.5, anchor='center')
    return control

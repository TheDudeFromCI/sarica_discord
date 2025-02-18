from typing import List, Optional
from prettytable import PrettyTable, TableStyle


def make_table(rows: List[List[str]], header: Optional[List[str]] = None):
    table = PrettyTable()
    table.set_style(TableStyle.SINGLE_BORDER)

    if header is not None:
        table.header = True
        table.field_names = header
    else:
        table.header = False

    for row in rows:
        table.add_row(row, divider=True)

    text = str(table)

    x = 0
    y = 0
    w = text.index("\n") - 1
    h = len(rows) * 2 + (2 if header is not None else 0)

    for i, c in enumerate(text):
        if c == "\n":
            x = 0
            y += 1
            continue

        if x == 0 and y == 0:
            text = text[:i] + "╔" + text[i + 1 :]
        elif x == 0 and y == h:
            text = text[:i] + "╚" + text[i + 1 :]
        elif x == w and y == 0:
            text = text[:i] + "╗" + text[i + 1 :]
        elif x == w and y == h:
            text = text[:i] + "╝" + text[i + 1 :]
        elif x == 0:
            text = text[:i] + "║" + text[i + 1 :]
        elif x == w:
            text = text[:i] + "║" + text[i + 1 :]
        elif y == 0:
            text = text[:i] + "═" + text[i + 1 :]
        elif y == h:
            text = text[:i] + "═" + text[i + 1 :]

        x += 1
    return text

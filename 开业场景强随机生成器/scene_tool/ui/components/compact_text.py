"""Fit a preview to measured available lines; preserve full text elsewhere."""


def fit_text(text, width, lines, measure):
    text = ' '.join(text.split())
    if width <= 0 or lines <= 0:
        return ''
    rows, current = [], ''
    for index, char in enumerate(text):
        if current and measure(current + char) > width:
            rows.append(current)
            current = ''
            if len(rows) == lines:
                last = rows[-1]
                while last and measure(last + '…') > width:
                    last = last[:-1]
                rows[-1] = last + '…'
                return '\n'.join(rows)
        current += char
    if current:
        rows.append(current)
    return '\n'.join(rows)

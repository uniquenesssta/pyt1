"""Normalize the independent per-field prompt visibility flags."""
def hidden_keys(hidden):
    if isinstance(hidden, dict):
        return {key for key, value in hidden.items() if value is True}
    return set(hidden or ())


def view_hidden(view):
    return {key for key, variable in getattr(view, 'hidden', {}).items() if variable.get()}

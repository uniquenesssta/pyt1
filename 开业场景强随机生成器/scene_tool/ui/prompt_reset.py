"""Restore the default prompt with one in-session undo snapshot."""
from scene_tool.config.defaults import DEFAULT_CONSTRAINTS
from scene_tool.domain.prompts import make_prompt
from scene_tool.domain.visibility import view_hidden
from scene_tool.config.product_size import FIXED_LARGE


class PromptResetController:
    def __init__(self, view):
        self.view = view
        self.snapshot = None

    def _cancel_pending(self):
        if self.view.pending:
            self.view.after_cancel(self.view.pending)
            self.view.pending = None

    @staticmethod
    def _replace(widget, text):
        widget.delete('1.0', 'end')
        widget.insert('1.0', text)

    def reset(self):
        view = self.view
        try:
            text = make_prompt(view.current(), view.industry.get(),
                               DEFAULT_CONSTRAINTS, view.copyline.get(), '', hidden=view_hidden(view),
                               render_style=view.render_style.get() if hasattr(view, 'render_style') else None,
                               product_size=view.product_size.get() if hasattr(view, 'product_size') else FIXED_LARGE)
        except ValueError as exc:
            view.status.set(str(exc))
            return False
        self._cancel_pending()
        before = {key: getattr(view, key).get('1.0', 'end-1c')
                  for key in ('constraints', 'extra', 'prompt')}
        before['rendered'] = view.rendered
        # Repeated clicks on an already reset prompt retain the useful snapshot.
        if (before['constraints'], before['extra'], before['prompt']) != (DEFAULT_CONSTRAINTS, '', text):
            self.snapshot = before
        self._replace(view.constraints, DEFAULT_CONSTRAINTS)
        self._replace(view.extra, '')
        view.set_prompt(text)
        view.undo_reset_button.configure(state='normal' if self.snapshot else 'disabled')
        if view.save():
            view.status.set('已复原默认提示词，当前参数与开业文案保留。可点“撤销复原”找回此前文字。')
        return True

    def undo(self):
        if self.snapshot is None:
            return False
        self._cancel_pending()
        view = self.view
        for key in ('constraints', 'extra', 'prompt'):
            self._replace(getattr(view, key), self.snapshot[key])
        view.rendered = self.snapshot['rendered']
        self.snapshot = None
        view.undo_reset_button.configure(state='disabled')
        if view.save():
            view.status.set('已恢复复原前的文字；场景参数未改变。')
        return True


"""预览筛选与表格显示，不修改完整改名计划。"""
import tkinter as tk


class PreviewMixin:
    def _visible_plans(self):
        selected = self.preview_filter_var.get()
        return [p for p in self.plans if selected == "全部" or p.status == selected]

    def _on_preview_filter_changed(self, _event=None):
        self._insert_plan_rows()
        self.set_busy(self.busy)

    def _insert_plan_rows(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        visible = self._visible_plans()
        self.preview_count_var.set(f"显示 {len(visible)} / 共 {len(self.plans)} 项")
        for plan in visible:
            lang = f"0x{plan.lang_id:04X}" if isinstance(plan.lang_id, int) else ""
            self.tree.insert(
                "",
                tk.END,
                values=(
                    plan.status,
                    plan.old_name,
                    plan.new_name,
                    plan.font_name,
                    plan.name_id if plan.name_id is not None else "",
                    lang,
                    plan.reason,
                ),
            )


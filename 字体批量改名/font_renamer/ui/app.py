from __future__ import annotations
import os
import queue
import threading
import traceback
import datetime as _dt
from typing import Optional
import tkinter as tk
from tkinter import filedialog, messagebox
from ..config import DEFAULT_EXTENSIONS, DEFAULT_NAME_IDS, DEFAULT_LANG_IDS, STATUS_RENAME, STATUS_SKIP, STATUS_ERROR, STATUS_DONE
from ..core.models import RenamePlan
from ..core.naming import parse_int_list
from ..core.reader import TTFont
from ..core.planning import build_rename_plan
from ..core.execution import execute_rename_plans
from ..storage.csv_log import write_csv_log
from ..core.scan_session import scan_session
from .layout import LayoutMixin
from .preview import PreviewMixin
from .preview_actions import PreviewActionsMixin

class FontRenamerApp(PreviewActionsMixin, PreviewMixin, LayoutMixin, tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("字体批量改名工具")
        self.geometry("1120x720")
        self.minsize(960, 600)

        self.busy = False
        self.scan_folder = ""
        self.scan_session = None
        self.protocol("WM_DELETE_WINDOW", self.request_close)
        self.work_queue: queue.Queue = queue.Queue()
        self.worker: Optional[threading.Thread] = None
        self.plans: list[RenamePlan] = []
        self.last_log_path: Optional[str] = None

        self.preview_filter_var = tk.StringVar(value="全部")
        self.preview_count_var = tk.StringVar(value="显示 0 / 共 0 项")
        self.folder_var = tk.StringVar()
        self.recursive_var = tk.BooleanVar(value=False)
        self.lower_ext_var = tk.BooleanVar(value=True)
        self.underscore_var = tk.BooleanVar(value=True)
        self.duplicate_var = tk.StringVar(value="自动添加数字后缀")
        self.name_ids_var = tk.StringVar(value=",".join(str(v) for v in DEFAULT_NAME_IDS))
        self.lang_ids_var = tk.StringVar(value="0x0804,0x0404,0x0C04,0x0409,0")
        self.ext_vars = {ext: tk.BooleanVar(value=True) for ext in DEFAULT_EXTENSIONS}

        self._preview_rows = {}
        self._create_widgets()
        self.create_preview_menu()
        self.after(100, self._drain_queue)

        if TTFont is None:
            messagebox.showwarning("缺少依赖", "未检测到 fontTools。\n请先在命令行运行：pip install fonttools")


    def require_session(self):
        if self.busy:
            return False
        if self.scan_session is None:
            messagebox.showinfo("请先扫描", "请先在主界面点击“扫描并预览”。")
            return False
        return True

    def open_duplicates(self):
        if self.require_session():
            from .duplicates import DuplicateWindow
            DuplicateWindow(self, self.scan_session)

    def open_same_names(self):
        if self.require_session():
            from .name_comparison import NameComparisonWindow
            NameComparisonWindow(self, self.scan_session)

    def request_close(self) -> None:
        if self.busy:
            messagebox.showinfo("正在处理", "请等待当前任务完成后关闭窗口。")
            return
        self.destroy()

    def choose_folder(self) -> None:
        folder = filedialog.askdirectory(title="选择包含字体文件的文件夹")
        if folder:
            self.folder_var.set(folder)

    def clear_results(self) -> None:
        if self.busy:
            return
        self.plans = []
        self.scan_session = None
        self.last_log_path = None
        self._insert_plan_rows()
        self.log_text.delete("1.0", tk.END)
        self.rename_btn.configure(state=tk.DISABLED)
        self.export_btn.configure(state=tk.DISABLED)

    def log(self, text: str) -> None:
        now = _dt.datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{now}] {text}\n")
        self.log_text.see(tk.END)

    def validate_inputs(self):
        folder = self.folder_var.get().strip().strip('"')
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("文件夹无效", "请选择一个有效的字体文件夹。")
            return None

        extensions = [ext for ext, var in self.ext_vars.items() if var.get()]
        if not extensions:
            messagebox.showerror("未选择格式", "请至少选择一种字体格式。")
            return None

        try:
            name_ids = parse_int_list(self.name_ids_var.get(), DEFAULT_NAME_IDS)
            lang_ids = parse_int_list(self.lang_ids_var.get(), DEFAULT_LANG_IDS)
        except Exception as exc:
            messagebox.showerror("参数错误", f"NameID 或语言优先级格式不正确：\n{exc}")
            return None

        return {
            "folder": folder,
            "extensions": extensions,
            "name_ids": name_ids,
            "lang_ids": lang_ids,
            "recursive": self.recursive_var.get(),
            "duplicate_mode": self.duplicate_var.get(),
            "lower_extension": self.lower_ext_var.get(),
            "use_underscore": self.underscore_var.get(),
        }

    def set_busy(self, busy: bool) -> None:
        self.busy = busy
        state = tk.DISABLED if busy else tk.NORMAL
        self.preview_filter.configure(state="disabled" if busy else "readonly")
        self.scan_btn.configure(state=state)
        self.export_btn.configure(state=(tk.DISABLED if busy or not self.plans else tk.NORMAL))
        can_rename = any(p.status == STATUS_RENAME for p in self._visible_plans())
        self.rename_btn.configure(state=(tk.DISABLED if busy or not can_rename else tk.NORMAL))
        if busy:
            self.progress.start(12)
        else:
            self.progress.stop()

    def scan_preview(self) -> None:
        if self.busy:
            return
        if TTFont is None:
            messagebox.showerror("缺少依赖", "请先安装 fontTools：\npip install fonttools")
            return

        config = self.validate_inputs()
        if not config:
            return

        self.clear_results()
        self.set_busy(True)
        self.log("开始扫描字体文件，只生成预览，不会改名。")

        def worker():
            try:
                session = scan_session(config, lambda text: self.work_queue.put(("log", text)))
                self.work_queue.put(("scan_done", session, config["folder"]))
            except Exception as exc:
                self.work_queue.put(("error", f"扫描失败：{exc}\n{traceback.format_exc()}"))

        self.worker = threading.Thread(target=worker, daemon=False)
        self.worker.start()

    def rename_files(self) -> None:
        if self.busy:
            return
        plans = [p for p in self._visible_plans() if p.status == STATUS_RENAME]
        todo_count = len(plans)
        if todo_count == 0:
            messagebox.showinfo("没有可改名文件", "当前预览中没有需要改名的文件。")
            return

        answer = messagebox.askyesno(
            "确认执行改名",
            f"当前筛选：{self.preview_filter_var.get()}\n即将重命名 {todo_count} 个字体文件。\n\n建议确认预览结果无误后再继续。是否执行？",
        )
        if not answer:
            return

        folder = self.scan_folder
        self.set_busy(True)
        self.log(f"开始执行改名，共 {todo_count} 个文件。")

        def worker():
            try:
                def thread_log(text: str) -> None:
                    self.work_queue.put(("log", text))

                success, failed = execute_rename_plans(plans, thread_log)
                try:
                    log_path = write_csv_log(folder, plans)
                except Exception as exc:
                    log_path = ""
                    thread_log(f"改名已执行，但 CSV 保存失败：{exc}；请重新导出结果。")
                self.work_queue.put(("rename_done", success, failed, log_path))
            except Exception as exc:
                self.work_queue.put(("error", f"改名失败：{exc}\n{traceback.format_exc()}"))

        self.worker = threading.Thread(target=worker, daemon=False)
        self.worker.start()

    def export_preview(self) -> None:
        if self.busy or not self.plans:
            return
        folder = self.scan_folder
        try:
            log_path = write_csv_log(folder, self.plans, prefix="font_rename_preview")
            self.last_log_path = log_path
            self.log(f"已导出预览 CSV：{log_path}")
            messagebox.showinfo("导出完成", f"已导出：\n{log_path}")
        except Exception as exc:
            messagebox.showerror("导出失败", str(exc))

    def _summarize(self) -> tuple[int, int, int, int]:
        rename_count = sum(1 for p in self.plans if p.status == STATUS_RENAME)
        done_count = sum(1 for p in self.plans if p.status == STATUS_DONE)
        skip_count = sum(1 for p in self.plans if p.status == STATUS_SKIP)
        error_count = sum(1 for p in self.plans if p.status == STATUS_ERROR)
        return rename_count, done_count, skip_count, error_count

    def _drain_queue(self) -> None:
        try:
            while True:
                item = self.work_queue.get_nowait()
                kind = item[0]

                if kind == "log":
                    self.log(item[1])

                elif kind == "scan_done":
                    _, session, folder = item
                    self.scan_session = session
                    plans = session.plans
                    self.plans = plans
                    for error in session.errors:
                        self.log(error)
                    self.scan_folder = folder
                    self._insert_plan_rows()
                    rename_count, _, skip_count, error_count = self._summarize()
                    self.log(f"扫描完成：将重命名 {rename_count} 个，跳过 {skip_count} 个，错误 {error_count} 个。")
                    if not plans:
                        self.log("没有找到符合扩展名设置的字体文件。")
                    self.set_busy(False)

                elif kind == "rename_done":
                    _, success, failed, log_path = item
                    self.scan_session = None
                    self.last_log_path = log_path
                    self._insert_plan_rows()
                    _, done_count, skip_count, error_count = self._summarize()
                    self.log(f"改名完成：成功 {success} 个，失败 {failed} 个。日志：{log_path or '保存失败，请重新导出'}")
                    self.set_busy(False)
                    messagebox.showinfo(
                        "处理完成",
                        f"成功改名：{success} 个\n失败：{failed} 个\n跳过：{skip_count} 个\n错误：{error_count} 个\n\n日志：\n{log_path or '保存失败，请重新导出预览 CSV'}",
                    )

                elif kind == "delete_done":
                    self.finish_preview_delete(item[1], item[2])

                elif kind == "error":
                    self.log(item[1])
                    self.set_busy(False)
                    messagebox.showerror("发生错误", item[1])
        except queue.Empty:
            pass
        finally:
            self.after(100, self._drain_queue)



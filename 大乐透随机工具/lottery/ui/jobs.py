"""工作线程仅处理数据，通过队列回到 Tk 主线程更新界面。"""
from queue import Empty, Queue
from threading import Event, Thread
import time
import traceback
from ..core.models import Cancelled


class Jobs:
    def __init__(self, root, status, busy):
        self.root, self.status, self.set_busy = root, status, busy
        self.queue = Queue()
        self.cancel = Event()
        self.running = False
        self.closed = False
        self.timer = root.after(60, self.poll)

    def start(self, work, done, failed):
        if self.running:
            self.status("请等待当前任务完成，或先取消")
            return False
        self.running = True
        self.cancel = Event()
        self.done, self.failed = done, failed
        self.set_busy(True)

        def run():
            last = 0.0

            def progress(text):
                nonlocal last
                now = time.monotonic()
                if now - last > 0.15:
                    self.queue.put(("progress", text))
                    last = now
            try:
                value = work(self.cancel, progress)
                if self.cancel.is_set():
                    raise Cancelled("操作已取消，上次结果已保留")
                self.queue.put(("done", value))
            except Cancelled as error:
                self.queue.put(("cancelled", str(error)))
            except Exception as error:
                self.queue.put(("error", (error, traceback.format_exc())))

        Thread(target=run, daemon=True).start()
        return True

    def poll(self):
        if self.closed:
            return
        try:
            while True:
                kind, value = self.queue.get_nowait()
                if kind == "progress":
                    self.status(value)
                    continue
                self.running = False
                self.set_busy(False)
                if kind == "done":
                    self.done(value)
                elif kind == "error":
                    self.failed(*value)
                else:
                    self.status(value)
        except Empty:
            pass
        finally:
            if not self.closed:
                self.timer = self.root.after(60, self.poll)

    def close(self):
        self.closed = True
        self.cancel.set()
        self.root.after_cancel(self.timer)

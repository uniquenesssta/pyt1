import threading
import unittest
from font_renamer.core.parallel import parallel_read


class ParallelReadTests(unittest.TestCase):
    def test_ten_concurrent_reads_keep_input_order_and_isolate_error(self):
        barrier = threading.Barrier(10, timeout=5)
        lock = threading.Lock()
        active = 0
        peak = 0
        def read(i):
            nonlocal active, peak
            with lock:
                active += 1
                peak = max(peak, active)
            try:
                barrier.wait()
                if i == 3: raise ValueError('bad font')
                return i * 2
            finally:
                with lock: active -= 1
        progress = []
        results = parallel_read(list(range(20)), read, lambda n,total: progress.append((n,total)))
        self.assertEqual(peak,10)
        for i,(value,error) in enumerate(results):
            if i == 3: self.assertIsInstance(error,ValueError)
            else:
                self.assertIsNone(error)
                self.assertEqual(value,i*2)
        self.assertEqual(progress[-1],(20,20))
        self.assertEqual(active,0)

    def test_empty_input(self):
        self.assertEqual(parallel_read([],lambda _: self.fail()),[])

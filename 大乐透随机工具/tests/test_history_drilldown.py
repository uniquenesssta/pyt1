from threading import Event
import unittest
from lottery.core.models import Draw,Ticket,Cancelled
from lottery.core.statistics import analyze,report_rows
from lottery.core.structure_profile import build_profile,domains
from lottery.core.history_drilldown import StatisticFilter,query_history
from lottery.core.querying import Query


class DrilldownTests(unittest.TestCase):
    def setUp(self):
        self.draws=[Draw(Ticket((1,2,3,4,5),(1,2)),'26001'),
                    Draw(Ticket((1,2,8,9,15),(3,4)),'26002'),
                    Draw(Ticket((1,2,3,24,25),(5,6)),'26003')]

    def test_all_report_counts_reconcile(self):
        for category,item,count,_,_ in report_rows(analyze(self.draws)):
            with self.subTest(category=category,item=item):
                rows,total,actual,_=query_history(self.draws,Query(),statistic=StatisticFilter('统计分析',category,item))
                self.assertEqual(actual,count)
                self.assertEqual(total,3)
                self.assertTrue(all('本期贡献' in detail for _,detail in rows))

    def test_all_structure_counts_reconcile(self):
        p=build_profile(self.draws,2)
        for category,keys in domains().items():
            for key in keys:
                rows,total,count,_=query_history(self.draws,Query(),2,StatisticFilter('结构权重',category,str(key)))
                self.assertEqual(count,p.counts[category][key])
                self.assertEqual(len(rows),count)
                self.assertEqual(total,2)

    def test_occurrences_differ_from_periods(self):
        rows,_,count,_=query_history(self.draws,Query(),statistic=StatisticFilter('统计分析','分区号码频率','1区 (01–07)'))
        self.assertEqual(count,10)
        self.assertEqual(len(rows),3)

    def test_recent_windows_and_query_intersection(self):
        data=[Draw(Ticket((1,2,3,4,5),(1,2)),str(26000+i)) for i in range(1,121)][::-1]
        for n in (50,100,17):
            rows,total,_,_=query_history(data,Query(),n)
            self.assertEqual(total,n)
            self.assertEqual(rows[-1][0].issue,'26120')
            self.assertEqual(int(rows[0][0].issue),26121-n)
        rows,total,_,_=query_history(data,Query('26120','期号','全部','完全一致'),50,StatisticFilter('统计分析','最长连号·互斥','5'))
        self.assertEqual(total,50);self.assertEqual(len(rows),1)

    def test_zero_and_duplicates_keep_source_semantics(self):
        data=self.draws+[self.draws[0]]
        f=StatisticFilter('统计分析','最长连号·互斥','5')
        self.assertEqual(query_history(data,Query(),statistic=f)[2],2)
        f=StatisticFilter('结构权重','最长连号','5')
        self.assertEqual(query_history(data,Query(),statistic=f)[2],1)
        f=StatisticFilter('结构权重','C1差值','31')
        self.assertEqual(query_history(data,Query(),statistic=f)[0],[])

    def test_invalid_and_cancel(self):
        with self.assertRaises(ValueError):query_history(self.draws,Query(),-1)
        event=Event();event.set()
        with self.assertRaises(Cancelled):query_history(self.draws,Query(),cancel=event)

    def test_double_click_resolves_clicked_sorted_row(self):
        from types import SimpleNamespace
        from lottery.ui.table import DataTable
        callbacks={};seen=[]
        tree=SimpleNamespace(bind=lambda event,callback:callbacks.update({event:callback}),
                             identify_region=lambda x,y:'cell',identify_row=lambda y:'1')
        table=SimpleNamespace(tree=tree,rows=[('sorted-first',),('clicked-second',)])
        DataTable.bind_open(table,seen.append)
        callbacks['<Double-1>'](SimpleNamespace(x=20,y=40))
        self.assertEqual(seen,[('clicked-second',)])
        tree.identify_region=lambda x,y:'heading'
        callbacks['<Double-1>'](SimpleNamespace(x=20,y=0))
        self.assertEqual(len(seen),1)

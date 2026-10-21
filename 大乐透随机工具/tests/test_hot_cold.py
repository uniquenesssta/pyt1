import unittest
from lottery.core.models import Draw,Ticket
from lottery.core.hot_cold import analyze_hot_cold
from lottery.core.history_drilldown import query_history,StatisticFilter
from lottery.core.querying import Query


class HotColdTests(unittest.TestCase):
    def setUp(self):
        self.draws=[Draw(Ticket((1,2,3,4,5) if i<=50 else (6,7,8,9,10),(1,2)),str(26000+i)) for i in range(1,101)]

    def test_50_100_sorted_window_and_complete_numbers(self):
        for n in (50,100):
            r=analyze_hot_cold(self.draws[::-1],n)
            self.assertEqual((r.total,r.last),(n,'26100'))
            self.assertEqual((len(r.front),len(r.back)),(35,12))
            self.assertEqual(sum(row[1] for row in r.front),n*5)
            self.assertEqual(sum(row[1] for row in r.back),n*2)
        r=analyze_hot_cold(self.draws,50)
        self.assertEqual(r.front[0],('06',50,'100.00%','热号'))
        self.assertEqual(next(row for row in r.front if row[0]=='01')[1:],(0,'0.00%','冷号'))

    def test_short_history_and_duplicates(self):
        r=analyze_hot_cold([self.draws[0]]*2,100)
        self.assertEqual(r.total,1)
        self.assertEqual(r.front[0][1],1)

    def test_equal_average_neutral(self):
        draws=[Draw(Ticket(tuple(range(i*5+1,i*5+6)),(1,2)),str(26001+i)) for i in range(7)]
        self.assertTrue(all(row[3]=='持平' for row in analyze_hot_cold(draws).front))

    def test_rows_match_drilldown(self):
        r=analyze_hot_cold(self.draws,50)
        for area,rows in [('前区',r.front),('后区',r.back)]:
            for number,count,_,_ in rows:
                results,_,actual,_=query_history(self.draws,Query(),50,StatisticFilter('统计分析',area+'·期数占比',number))
                self.assertEqual(actual,count);self.assertEqual(len(results),count)

    def test_empty_invalid_and_conflict(self):
        with self.assertRaises(ValueError):analyze_hot_cold([])
        with self.assertRaises(ValueError):analyze_hot_cold(self.draws,17)
        with self.assertRaises(ValueError):analyze_hot_cold([self.draws[0],Draw(Ticket((2,3,4,5,6),(1,2)),'26001')])

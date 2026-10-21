from dataclasses import replace
import random
import unittest
from lottery.core.models import Draw,Ticket
from lottery.core.history_window import select_window
from lottery.core.structure_profile import build_profile,structure_values
from lottery.core.structure_scoring import StructureScorer
from lottery.core.generation import GenerationConfig,MODES,generate


def draw(issue,front=(1,2,8,9,15)):
    return Draw(Ticket(front,(1,2)),str(issue))


class StructureProfileTests(unittest.TestCase):
    def test_50_100_custom_and_all_order(self):
        draws=[draw(26000+i) for i in range(1,121)][::-1]
        for n,expected in [(50,26071),(100,26021),(17,26104),(0,26001)]:
            selected,order=select_window(draws,n)
            self.assertEqual(int(selected[0].issue),expected)
            self.assertEqual(selected[-1].issue,'26120')
        self.assertEqual(len(select_window(draws,200)[0]),120)

    def test_issue_dedup_conflict_and_missing(self):
        self.assertEqual(len(select_window([draw(26001)]*2,50)[0]),1)
        with self.assertRaises(ValueError):select_window([draw(26001),draw(26001,(1,2,3,4,5))])
        with self.assertRaises(ValueError):select_window([draw(26001),draw('')])
        with self.assertRaises(ValueError):select_window([draw(26001)],-1)

    def test_feature_details(self):
        values=structure_values((1,2,8,9,15))
        self.assertEqual([values[f'C{i}差值'] for i in range(1,5)],[1,6,1,6])
        self.assertEqual(values['连号形态'],'2+2+1')
        self.assertEqual(values['最长连号'],2)
        self.assertEqual(values['空区数量'],2)
        self.assertEqual(values['4区空区'],1)
        values=structure_values((1,2,3,24,25))
        self.assertEqual(values['最大跨区（差值>7）'],3)
        self.assertEqual(values['2区中间覆盖（差值>10）'],1)

    def test_mean_and_distribution_are_separate(self):
        p=build_profile([draw(26001),draw(26002,(1,4,8,12,16))])
        self.assertEqual(p.means['C1差值'],2)
        self.assertEqual(p.counts['C1差值'][2],0)
        self.assertAlmostEqual(sum(p.weights['C1差值'].values()),100)
        self.assertGreater(p.weights['C1差值'][2],0)

    def test_window_changes_used_weights(self):
        draws=[draw(26000+i,(1,2,3,4,5) if i<=50 else (1,3,5,7,9)) for i in range(1,101)]
        short,long=build_profile(draws,50),build_profile(draws,100)
        self.assertEqual(short.counts['最长连号'][5],0)
        self.assertEqual(long.counts['最长连号'][5],50)
        self.assertNotEqual(StructureScorer(short).weight((1,2,3,4,5)),StructureScorer(long).weight((1,2,3,4,5)))

    def test_all_indicators_disabled_and_invalid_weights(self):
        p=build_profile([draw(26001)])
        p.strengths={name:0 for name in p.strengths}
        self.assertEqual(StructureScorer(p).weight((1,2,3,4,5)),1)
        p.weights['C1差值'][1]=float('nan')
        with self.assertRaises(ValueError):p.validate()

    def test_manual_weights_reach_generated_tickets(self):
        p=build_profile([draw(26001)])
        p.weights['C1差值']={k:100.0 if k==2 else 0.0 for k in p.weights['C1差值']}
        config=GenerationConfig(count=30,mode=MODES[2],front_excluded=tuple(range(11,36)),structure_profile=p)
        tickets=generate(config,rng=random.Random(12))
        self.assertTrue(all(t.front[1]-t.front[0]==2 for t in tickets))
        p.weights['C1差值']={k:100.0 if k==31 else 0.0 for k in p.weights['C1差值']}
        with self.assertRaisesRegex(ValueError,'没有可用'):generate(config)

    def test_uniform_unaffected(self):
        p=build_profile([draw(26001)])
        a=GenerationConfig(count=10)
        self.assertEqual(generate(a,rng=random.Random(1)),generate(replace(a,structure_profile=p),rng=random.Random(1)))

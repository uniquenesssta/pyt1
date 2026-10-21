from copy import deepcopy
from dataclasses import replace
from threading import Event
from unittest.mock import patch
import random
import unittest
from lottery.core.generation import GenerationConfig,MODES,generate
from lottery.core.structure_cache import StructureCache
from lottery.core.structure_profile import build_profile
from lottery.core.models import Draw,Ticket,Cancelled


class StructureCacheTests(unittest.TestCase):
    def setUp(self):
        self.draws=[Draw(Ticket((1,2,8,9,15),(1,2)),str(26000+i)) for i in range(1,121)]
        self.profile=build_profile(self.draws,50)
        self.config=GenerationConfig(count=20,mode=MODES[2],structure_profile=self.profile,
                                     front_excluded=tuple(range(13,36)))
        self.cache=StructureCache()

    def run_generation(self, config=None, seed=123, cancel=None):
        return generate(config or self.config, rng=random.Random(seed), cancel=cancel,structure_cache=self.cache)

    def test_repeat_reuses_pool_but_not_results(self):
        a=self.run_generation()
        with patch('lottery.core.structure_cache.StructurePool',side_effect=AssertionError('must not rebuild')):
            b=self.run_generation(seed=456)
        self.assertNotEqual(a,b)
        self.assertEqual((self.cache.builds,self.cache.hits),(1,1))
        self.assertEqual(a,self.run_generation(seed=123))

    def test_cached_and_uncached_identical(self):
        expected=generate(self.config,rng=random.Random(123))
        self.assertEqual(expected,self.run_generation())
        self.assertEqual(expected,self.run_generation())

    def test_irrelevant_options_reuse_front_pool(self):
        self.run_generation()
        result=self.run_generation(replace(self.config,count=4,unique=False,back_fixed=(12,),back_excluded=(1,2)))
        self.assertEqual(self.cache.builds,1)
        self.assertTrue(all(12 in t.back and not set(t.back)&{1,2} for t in result))

    def test_relevant_changes_invalidate(self):
        self.run_generation()
        variants=[replace(self.config,front_fixed=(1,)),
                  replace(self.config,front_excluded=tuple(range(12,36))),
                  replace(self.config,structure_profile=build_profile(self.draws,100))]
        p=deepcopy(self.profile);p.weights['C1差值'][1]+=1
        variants.append(replace(self.config,structure_profile=p))
        p=deepcopy(self.profile);p.strengths['C1差值']=2
        variants.append(replace(self.config,structure_profile=p))
        changed=list(self.draws);changed[-1]=Draw(Ticket((1,3,8,9,15),(1,2)),'26120')
        variants.append(replace(self.config,structure_profile=build_profile(changed,50)))
        for config in variants:
            old=self.cache.builds;self.run_generation(config)
            self.assertEqual(self.cache.builds,old+1)

    def test_mutated_profile_does_not_mutate_cached_pool(self):
        before=self.run_generation()
        self.profile.weights['C1差值'][1]+=9
        self.run_generation()
        self.assertEqual(self.cache.builds,2)
        self.assertEqual(before,generate(replace(self.config,structure_profile=build_profile(self.draws,50)),rng=random.Random(123)))

    def test_cancelled_build_not_published(self):
        cancel=Event()
        with self.assertRaises(Cancelled):
            generate(self.config,cancel=cancel,progress=lambda _:cancel.set(),structure_cache=self.cache)
        self.assertEqual(self.cache.builds,0)
        self.run_generation();self.assertEqual(self.cache.builds,1)
        cancel.set()
        with self.assertRaises(Cancelled):self.run_generation(cancel=cancel)

    def test_failure_preserves_last_complete_entry(self):
        self.run_generation()
        p=deepcopy(self.profile);p.weights['C1差值']={k:100 if k==31 else 0 for k in p.weights['C1差值']}
        with self.assertRaisesRegex(ValueError,'没有可用'):
            self.run_generation(replace(self.config,structure_profile=p))
        self.run_generation();self.assertEqual((self.cache.builds,self.cache.hits),(1,1))

    def test_clear_and_bounded_single_entry(self):
        self.run_generation()
        self.run_generation(replace(self.config,structure_profile=build_profile(self.draws,100)))
        self.run_generation();self.assertEqual(self.cache.builds,3)
        self.cache.clear();self.run_generation();self.assertEqual(self.cache.builds,4)

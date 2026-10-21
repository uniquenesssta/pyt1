from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock
import random
import tkinter as tk
import unittest
from lottery.core.cross_weights import CROSS_GROUPS, cross_values, resolve_cross_overrides
from lottery.core.generation import GenerationConfig,MODES,generate
from lottery.core.models import Draw,Ticket
from lottery.core.structure_profile import build_profile
from lottery.ui.cross_link import CrossWeightLink


class CrossLinkTests(unittest.TestCase):
    def setUp(self):
        self.draws=[Draw(Ticket((1,2,8,9,15),(1,2)),str(26000+i)) for i in range(1,121)]
        self.interp=tk.Tcl()
        def var(value):return tk.StringVar(master=self.interp,value=value)
        self.controls=SimpleNamespace(fill_button=Mock(),cross_period=var('跟随结构权重页'),
            weight_vars=[[var('1') for _ in range(5)] for _ in range(2)],
            custom=tk.BooleanVar(master=self.interp,value=False),mode=var(MODES[0]),
            update_mode=Mock(),cross_source=var(''))
        self.page=SimpleNamespace(profile=build_profile(self.draws,50),draws=self.draws,
                                  period=var('50'),describe=Mock(),render=Mock())
        self.page.snapshot=lambda:self.page.profile
        self.errors=[]
        self.link=CrossWeightLink(self.controls,self.page,self.errors.append)

    def test_fill_current_preserves_edits_and_enables_mode(self):
        self.page.profile.weights[CROSS_GROUPS[0]][0]=43.25
        self.link.fill()
        self.assertFalse(self.errors)
        self.assertTrue(self.controls.custom.get())
        self.assertEqual(self.controls.mode.get(),MODES[2])
        self.assertEqual(float(self.controls.weight_vars[0][0].get()),43.25)

    def test_editors_share_profile_even_before_first_fill(self):
        expected = cross_values(self.page.profile)[0][1]
        self.assertEqual(float(self.controls.weight_vars[0][1].get()), expected)
        self.controls.weight_vars[0][1].set('42')
        self.assertEqual(self.page.profile.weights[CROSS_GROUPS[0]][1], 42)

    def test_reselect_100_custom_all(self):
        for choice,size in [('100',100),('17',17),('全部',120)]:
            self.controls.cross_period.set(choice);self.link.fill()
            self.assertEqual(len(self.page.profile.draws),size)
            self.assertEqual(self.page.period.get(),choice)
            self.assertEqual(self.controls.cross_period.get(),'跟随结构权重页')

    def test_both_directions_and_invalid_input(self):
        self.link.fill()
        self.controls.weight_vars[0][1].set('67.5')
        self.assertEqual(self.page.profile.weights[CROSS_GROUPS[0]][1],67.5)
        self.controls.weight_vars[0][1].set('')
        self.assertEqual(self.page.profile.weights[CROSS_GROUPS[0]][1],67.5)
        self.page.profile=build_profile(self.draws,100)
        self.page.on_change(self.page.profile)
        self.assertEqual(float(self.controls.weight_vars[0][1].get()),cross_values(self.page.profile)[0][1])

    def test_invalid_period_preserves_profile(self):
        old=self.page.profile
        self.controls.cross_period.set('-1');self.link.fill()
        self.assertIs(self.page.profile,old);self.assertEqual(len(self.errors),1)

    def test_override_is_not_multiplied_twice(self):
        profile=self.page.profile
        values=cross_values(profile)
        base=GenerationConfig(count=30,mode=MODES[2],front_excluded=tuple(range(15,36)),structure_profile=profile)
        filled=replace(base,max_span_weights=values[0],start_span_weights=values[1])
        resolved=resolve_cross_overrides(filled)
        self.assertEqual(resolved.max_span_weights,())
        self.assertEqual(generate(base,rng=random.Random(123)),generate(filled,rng=random.Random(123)))
        manual=resolve_cross_overrides(replace(filled,max_span_weights=(100,0,0,0,0)))
        self.assertEqual(manual.structure_profile.weights[CROSS_GROUPS[0]][0],100)
        self.assertNotEqual(profile.weights[CROSS_GROUPS[0]][0],100)

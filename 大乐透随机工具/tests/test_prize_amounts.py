"""核对奖金数据来源、普通复式汇总和缺失金额的表示。"""
from dataclasses import replace
import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from lottery.core.models import Draw, Ticket
from lottery.core.prize_amounts import basic_amount
from lottery.core.prize_match import compare_pick
from lottery.data.prize_notices import parse_prize_page
from lottery.ui.prize_amount_panel import PrizeAmountPanel, draw_key


DRAW = Draw(Ticket((2, 9, 16, 26, 35), (6, 11)), "26132", draw_date="2026-11-18")
ACTUAL_AMOUNTS = (8814866, 101697, 5000, 300, 150, 15, 5)


def sample_page(amounts=ACTUAL_AMOUNTS):
    rows = [{"Name": f"{name}等奖", "WinMoney": amount}
            for name, amount in zip("一二三四五六七", amounts)]
    rows.append({"Name": "追加一等奖", "WinMoney": 7051893})
    return ("""<div class="gg_ssq gg_dlt"><dl>
<span class="ggissue_name">大乐透第<strong>26132</strong>期</span>
<p class="number dlt-number"><span>02</span><span>09</span><span>16</span><span>26</span><span>35</span>
<span class='lq'>06</span><span class='lq'>11</span></p>
<dd id="openDate">开奖日期：2026年11月18日</dd></dl></div>
<p class="number dlt-number"><span>01</span></p>"""
            + f"<script>var issue_current_WinType = JSON.parse('{json.dumps([rows], ensure_ascii=False)}');</script>")


class PrizeAmountTests(unittest.TestCase):
    def test_by_issue_and_actual_winning_tiers(self):
        amounts = parse_prize_page(sample_page(), replace(DRAW, issue="2026132"))
        self.assertEqual(amounts, ACTUAL_AMOUNTS)
        single = compare_pick(Ticket((1, 2, 9, 16, 26), (1, 6)), DRAW)
        self.assertEqual(basic_amount(single.prizes, amounts), (300, ()))
        compound = compare_pick(Ticket((1, 2, 9, 16, 26), (1, 6, 11)), DRAW)
        self.assertEqual(basic_amount(compound.prizes, amounts), (5600, ()))

    def test_missing_top_prize_is_not_a_zero_payout(self):
        amounts = parse_prize_page(sample_page((0, *ACTUAL_AMOUNTS[1:])), DRAW)
        self.assertIsNone(amounts[0])
        self.assertEqual(basic_amount(((1, 1), (7, 3)), amounts), (15, (1,)))

    def test_rejects_wrong_issue_numbers_date_and_unreadable_page(self):
        for altered in (replace(DRAW, issue="26131"), replace(DRAW, draw_date="2026-11-16"),
                        replace(DRAW, ticket=Ticket((1, 9, 16, 26, 35), (6, 11)))):
            with self.assertRaisesRegex(ValueError, "不一致"):
                parse_prize_page(sample_page(), altered)
        with self.assertRaisesRegex(ValueError, "本期开奖区"):
            parse_prize_page("<html>开奖接口暂不可用</html>", DRAW)

    def test_selected_amount_distinguishes_unpaid_from_zero_and_partial_total(self):
        win = compare_pick(Ticket((1, 2, 9, 16, 26), (1, 6)), DRAW)
        lose = compare_pick(Ticket((1, 3, 5, 7, 11), (2, 3)), DRAW)
        entries = [(None, DRAW, win, ""), (None, DRAW, lose, ""), (None, None, None, "待开奖数据")]
        panel = SimpleNamespace(notices={}, label=Mock(), sync=Mock())
        PrizeAmountPanel.show(panel, entries)
        self.assertIn("1 期奖金待查", panel.label.configure.call_args.kwargs["text"])
        self.assertEqual(list(panel.pending.values()), [DRAW])
        panel.notices[draw_key(DRAW)] = ACTUAL_AMOUNTS
        PrizeAmountPanel.show(panel, entries)
        self.assertIn("已知 300 元 · 1 条尚无对应开奖", panel.label.configure.call_args.kwargs["text"])
        PrizeAmountPanel.show(panel, entries[1:2])
        self.assertTrue(panel.label.configure.call_args.kwargs["text"].endswith("：0 元"))

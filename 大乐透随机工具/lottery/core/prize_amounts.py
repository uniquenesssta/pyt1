"""将实际公布的基本投注单注奖金乘中得的注数，不把未知奖金当作零。"""


def basic_amount(prizes, amounts):
    total = 0
    missing = []
    for level, count in prizes:
        amount = amounts[level - 1]
        if amount is None:
            missing.append(level)
        else:
            total += count * amount
    return total, tuple(missing)

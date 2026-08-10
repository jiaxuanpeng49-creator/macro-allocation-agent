def judge_cycle(factors):

    growth = factors["growth"]
    inflation = factors["inflation"]

    if growth == 1 and inflation == -1:
        return "复苏"

    elif growth == 1 and inflation == 1:
        return "过热"

    elif growth == -1 and inflation == 1:
        return "滞胀"

    elif growth == -1 and inflation == -1:
        return "衰退"

    else:
        return "中性"
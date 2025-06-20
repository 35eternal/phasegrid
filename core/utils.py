# scripts/utils.py

def calculate_implied_prob(odds):
    if odds < 0:
        return round((-odds) / (-odds + 100) * 100, 2)
    else:
        return round(100 / (odds + 100) * 100, 2)

def calculate_ev(model_prob, odds):
    imp = calculate_implied_prob(odds)
    edge = (model_prob - imp) / 100
    payout = (100 if odds < 0 else odds)
    risk = (abs(odds) if odds < 0 else 100)
    return round(edge * payout, 2)

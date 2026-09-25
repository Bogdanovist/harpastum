import numpy as np
"""
Utility functions.
"""

def compare_roll(odds,draw):
    log_odds = np.log(odds)
    chance = np.exp(log_odds)/(1. + np.exp(log_odds))
    roll = np.random.random()
    if abs(roll-chance) < draw:
        return 0
    elif roll < chance:
        return 1
    else:
        return -1

def bracket(vmin,val,vmax):
    """
    Returns the value, ensuring it sits within supplied limits.
    """
    val = min(val,vmax)
    val = max(val,vmin)
    return val

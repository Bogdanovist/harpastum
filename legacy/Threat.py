"""
Utility routines for assessing threats.
"""
import numpy as np
from Vector import *
import pdb as debug

def threat_score(p,d):
    # magic numbers
    min_fac=1.
    max_fac=5.
    # These number above mean that directly in front is 5 times worse than directly behind
    
    # Find angle factor between the two player and direction of attack.
    # Maximised if the defender is exactly in our way, minimised if they are behind the attacker.
    diff = d.pos - p.pos
    afac = (Vector(1*p.direction,0).angle_factor(diff) + 1)/2.
    # 1/dist ensures that large threats and worse than small ones
    return 1/diff.mag2() * ( (max_fac-min_fac)*afac + min_fac ) 

def rx_threat(rx,full=False):
    """
    Threat assessment for a potential Rx.
    """
    
    defenders = [ p for p in rx.opposite_team.players.values() if p.standing ]
    if len(defenders) == 0:
        if full:
            return 0, [], []
        else:
            return 0

    threats = [ threat_score(rx,p) for p in defenders ]

    imax = np.argmax(threats)
    if full:
        return threats[imax], threats, defenders
    else:
        return threats[imax]

def bc_threat(bc):
    """
    Threat assessment for the bc.
    """
    # NOTE: Only works if Team in TeamAttack state (but doesn't check)
    # NOTE: Won't work well if the BC isn't running downfield, would need to alter how they percieved
    # threat from behind in this case. Current behaviour not valid for sitting in a pocket.
    # NOTE: Will never pass if BN not threatened...

    defenders = [ p for p in bc.team.state.unblocked_opponents if p.standing ]
    if len(defenders) == 0:
        return 0.

    threats = [ threat_score(bc,p) for p in defenders ]
    
    imax = np.argmax(threats)
    return threats[imax]
    

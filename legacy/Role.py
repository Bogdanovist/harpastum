import Player
"""
Different roles implemented as different class for conveniance. However, they details are actually all
just softcoded in the self.config dictionary. This allows easier configuration from info stored as set
by the manager.
"""

class Role(dict):
    """
    Defines the players role (or position). This is the strategic level of the player AI, that
    determines what States should be used in what different ball states.
    """
    def __init__(self):
        # NOTE: Acts as a blocker only in attack. Need to implement utility player.

        self.update([ ('ball_loose',Player.PlayerBallLoose),\
                                 ('ball_flying',Player.PlayerBallFlying),\
                                 ('ball_carrier',Player.PlayerBallCarrier),\
                                 ('defence',Player.PlayerDefence),\
                                 ('attack',Player.BlockerAttack)])

class DefenderRole(Role):
    def __init__(self):
        self.update([ ('ball_loose',Player.PlayerBallLoose),\
                                 ('ball_flying',Player.PlayerBallFlying),\
                                 ('ball_carrier',Player.PlayerBallCarrier),\
                                 ('defence',Player.DefenderDefence),\
                                 ('attack',Player.BlockerAttack)])

class BlockerRole(Role):
    def __init__(self):
        self.update([ ('ball_loose',Player.PlayerBallLoose),\
                                 ('ball_flying',Player.PlayerBallFlying),\
                                 ('ball_carrier',Player.PlayerBallCarrier),\
                                 ('defence',Player.PlayerDefence),\
                                 ('attack',Player.BlockerAttack)])

class RxRole(Role):
    def __init__(self):
        self.update([ ('ball_loose',Player.PlayerBallLoose),\
                                 ('ball_flying',Player.PlayerBallFlying),\
                                 ('ball_carrier',Player.PlayerBallCarrier),\
                                 ('defence',Player.PlayerDefence),\
                                 ('attack',Player.RxAttack)])

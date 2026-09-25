import Player
import Entity
import State
import MoveState
import MessageHandler
import pdb as debug
import numpy as np

class Team(Entity.Entity):
    """
    A container for a team.
    """
    
    def __init__(self,message_handler,direction):
        """
        Direction sets the attack direction (via sign).
        """
        super(Team,self).__init__(message_handler)
        self.players=dict()
        self.direction=direction
        self.opposite_team=None
        self.nearest_defender_updated=-1.

    @property
    def attack_end_zone_x(self):
        if self.direction > 0.:
            return self.pitch.xsize
        else:
            return 0.

    @property
    def defend_end_zone_x(self):
        if self.direction > 0.:
            return 0.
        else:
            return self.pitch.xsize

    @property
    def in_possession(self):
        if self.pitch.ball.carrier.team == self:
            return True
        else:
            return False
    
    @property
    def nearest_defender(self):
        if not self.in_possession:
            return None
        else:
            if self.nearest_defender_updated < self.pitch.game_time:
                defs = [ p for p in self.opposite_team.players.values() ]
                d2 = [ (p.pos - self.pitch.ball.carrier).mag2() for p in defs]
                self._nearest_defender = defs[np.argmin(d2)]
                self.nearest_defender_updated = self.pitch.game_time
        return self._nearest_defender

    def setup(self):
        # NOTE: Team setup actions?
        pass
    
    def add_player(self,p):
        self.players[p.uid] = p
        p.team=self
        # Add to contacts for message passing
        self.register(p)

    def get_message(self,msg):
        """
        Only message content looked at.
        """
        if msg.subject == "ball_flying":
            self.state = TeamBallFlying(self)
        elif msg.subject == "ball_loose":
            self.state = TeamBallLoose(self)
        elif msg.subject == "ball_held":
            if self.in_possession:
                self.state = TeamAttack(self)
            else:
                self.state = TeamDefence(self)
        elif msg.subject == "setup":
            self.setup()
        else:
            if not self.state.get_message(msg):
                #raise Exception("Unknown message:" + msg.subject + " recived")        
                print("Uncaught message " + msg.subject)

class TeamBallLoose(State.State):

    pass
        
class TeamAttack(State.State):
    
    def enter(self):
        # Magic numbers
        self.block_assignment_update_period = 0. # in seconds
        this=self.owner
        self.assign_blocks()

    def execute(self):
        """
        Periodically re-assign blocking targets.
        """
        this=self.owner
        self.block_update -= this.pitch.dt

        if self.block_update <= 0.:
            self.assign_blocks()
    
    def get_message(self,msg):
        if msg.subject == 'block_target_down':
            self.assign_blocks()
            return True
        else:
            return False

    def assign_blocks(self):
        # NOTE: Should consider defenders (block at the rear) and midfielders if needed as well as blockers.
        this=self.owner
        bc=this.pitch.ball.carrier

        # Find all standing blockers and standing defenders
        blockers = [ p for p in this.players.values() if type(p.move_state) == MoveState.Block and not p.has_ball\
                         and p.standing]
        defenders = [ p for p in this.opposite_team.players.values() if p.standing ]
        # Find d2 for all defenders-BC
        dlist = [ (p.pos-bc.pos).mag2() for p in defenders ]

        self.unblocked_opponents=list()

        while len(defenders) > 0 and len(blockers) > 0:
            # Find closest defender
            iclosest = np.argmin(dlist)
            closest = defenders.pop(iclosest)
            dnow = dlist.pop(iclosest)
            # Find nearest blocker
            blist = [ (p.pos-closest.pos).mag2() for p in blockers ]
            blocker = blockers.pop(np.argmin(blist))
            # Assign blocking target
            msg = MessageHandler.Message(blocker,this,'block_target',(closest,bc))
            this.message_handler.add(msg)
            # Check if we think we can safely block this target or not
            # NOTE: Simple comparison of distance, can do much better
            if dnow < (blocker.pos - bc.pos).mag2():
                self.unblocked_opponents.append(closest)
        self.block_update = self.block_assignment_update_period  
        
        # Check for any leftover un-blocked players. These are dangerous
        if len(defenders) > 0:
            for p in defenders:
                self.unblocked_opponents.append(p)

class TeamDefence(State.State):
    
    def enter(self):
        # Magic numbers
        self.defence_assignment_update_period = 0. # in seconds
        this=self.owner
        self.assign_defence()

    def get_message(self,msg):
        if msg.subject == 'defensive_target_down':
            self.assign_defence()
            return True
        else:
            return False    

    def execute(self):
        """
        Periodically re-assign blocking marking targets.
        """
        this=self.owner
        self.defence_update -= this.pitch.dt

        if self.defence_update <= 0.:
            self.assign_defence()
    
    def assign_defence(self):
        # Magic number
        push_up_limit=30.

        this=self.owner
        # NOTE: This implements a single defensive line. We could allow more fancy formations to be specified.
        # NOTE: Should probably use projections of positions instead of just current position.
                        
        defenders = [ p for p in this.players.values() if type(p.move_state) == MoveState.Defend and p.standing ]
        attackers = [ p for p in this.opposite_team.players.values() if p.standing and \
                          p.dist_to_attack_end_zone < push_up_limit ]

        # Iterate over attackers, assign the closest defender to the most threatening attacker until none of one set left.
        # NOTE: Assumes distance to end zone the only measure of threat
        # NOTE: 1/dist to make 'higher number more threatening'
        threats = [ 1./p.dist_to_attack_end_zone for p in attackers ]
        
        while len(defenders) > 0 and len(attackers) > 0:
            ithreat = (np.argmax(threats))
            attacker = attackers.pop(ithreat)
            threat = threats.pop(ithreat)
            dlist = [ (p.pos - attacker.pos).mag2() for p in defenders ]
            defender = defenders.pop(np.argmin(dlist))
            # Assign marking target
            this.message_handler.add( MessageHandler.Message(defender,this,'defensive_target',attacker))
            
        self.defence_update = self.defence_assignment_update_period

class TeamBallFlying(State.State):
    pass

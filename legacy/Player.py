import Entity
import State
import MoveState
import Pitch
import Team
from Vector import Vector
import Steering
import Threat
import pdb as debug
import Utils
import numpy as np
import MessageHandler
import Ball
import Role
import math

class Player(Entity.Entity):
    """
    Player base class. Implements a general all-rounder position.
    """
    def __init__(self,message_handler,role,pitch,xstart,ystart,top_speed=10.,acc=10.,strength=5.,throw_power=30.,\
                 stamina=100.,tough=100.,block_skill=5.,catch_skill=70.,mass=1.):
        super(Player,self).__init__(message_handler)
        self.team=None
        self.role=role
        self.pitch=pitch
        self.size=1.
        self.xstart=xstart
        self.ystart=ystart
        self.top_speed=top_speed
        self.top_acc=acc
        self.stamina=stamina
        self.tough=tough
        self.strength=strength
        self.throw_power=throw_power
        self.block_skill=block_skill
        self.catch_skill=catch_skill
        self.mass=mass
        # Experimental linear drag locomotion model
        self.drag = self.top_acc/self.top_speed
        # Damage and exhaustion counters
        self.puff = self.stamina
        self._health = self.tough 
        self._state = None
        self._move_state = None

    def setup(self):
        """
        Call to reset to neutral state at starting position.
        """
        self.pos = Vector(self.xstart,self.ystart)
        self.vel = Vector(0.,0.)
        self.acc = Vector(0.,0.)
        self.standing=True
        self._prone=-1.
        # Are we trying to catch the ball?
        self.want_to_catch=True
        self._state=None
        self._move_state=None

    @property
    def move_state(self):
        return self._move_state
    
    @move_state.setter
    def move_state(self,new_state):
        try:
            self._move_state.exit()
        except:
            pass
        finally:
            self._move_state=new_state        
            self._move_state.enter()

    @property
    def prone(self):
        return self._prone
    
    @prone.setter
    def prone(self,value):
        if value < 0.:
            self.standing = True
        else:
            self.standing = False
            if self.has_ball:
                self.drop_ball()
            if self.in_contact:
                self.pitch.remove_all_contact(self)
        self._prone=value
    
    @property
    def health(self):
        return self._health

    @health.setter
    def health(self,value):
        if value < 0.:
            msg = (self.team,self,'tap_out')
            self.message_handler.add(msg)

    def get_message(self,msg):
        """
        Only messages content looked at for the moment.
        """

        if msg.subject == "ball_flying":
            self.state = self.role['ball_flying'](self)
        elif msg.subject == "ball_loose":
            self.state = self.role['ball_loose'](self)
        elif msg.subject == "ball_held":
            if self.has_ball:
                self.state = self.role['ball_carrier'](self)
            elif self.team_in_possession:
                self.state = self.role['attack'](self)
            else:
                self.state = self.role['defence'](self)
        elif msg.subject == "setup":
            self.setup()
        else:
            if not self.state.get_message(msg):
                if not self.move_state.get_message(msg):
                    print("Uncaught message " + msg.subject)    
    
    @property
    def attack_end_zone_x(self):
        return self.team.attack_end_zone_x
    
    @property
    def defend_end_zone_x(self):
        return self.team.defend_end_zone_x

    @property
    def dist_to_attack_end_zone(self):
        return (self.attack_end_zone_x - self.x)*self.team.direction

    @property
    def dist_to_defend_end_zone(self):
        return (self.x - self.defend_end_zone_x)*self.team.direction

    @property
    def opposite_team(self):
        return self.team.opposite_team

    @property
    def direction(self):
        return self.team.direction    

    @property
    def has_ball(self):
        return self.pitch.ball.carrier == self

    @property
    def in_contact(self):
        return self in self.pitch.contacts.keys()

    @property
    def team_name(self):
        if self.team.direction > 0:
            return('home')
        else:
            return('away')

    @property
    def team_in_possession(self):
        return self.team.in_possession

    def x_from_defend_end_zone(self,x):
        if self.team.direction > 0:
            return x
        else:
            return self.pitch.xsize-x  

    def move(self):

        # NOTE: Ignores mass! (assumes m=1 I guess)
        # Don't move if we are prone
        if not self.standing:
            # Prone players might still be moving, but they rapidly deccelerate!
            # Magic numbers
            prone_acc = 20.
            prone_top_speed = 5.
            desired_acc = self.vel.norm() * prone_acc * self.pitch.dt * -1.
            if self.vel.mag() < desired_acc.mag():
                self.vel=Vector(0,0)
            else:
                self.vel += desired_acc
                self.vel = self.vel.truncate(prone_top_speed)
                self.pos += self.vel * self.pitch.dt
            return
        elif self.in_contact:
            # Push resolved seperately
            return
        acc = self.current_acc()
        # Check current puff reduced acc
        # NOTE HACK: Current states consider current vel in providing desired acc
        # We undo this so that they return the actual desired velocity
        state_vel = self.move_state.execute()
        desired_vel = state_vel + self.vel 
        drag_limited_acc = acc * (1. - desired_vel.angle_factor(self.vel) * self.vel.mag() / self.top_speed)
        desired_acc = (desired_vel - self.vel).truncate(drag_limited_acc)
        self.vel += desired_acc * self.pitch.dt
        self.vel = self.vel.truncate(self.top_speed)
        self.pos += self.vel * self.pitch.dt
        # It costs puff to move
        self.puff -= desired_acc.mag() * self.pitch.dt * self.pitch.puff_fac

    def push(self):
        if not self.in_contact: return
        # NOTE: Pushing forwards always, but we don't always want to do that. Need to have hook
        # into state and define in states the push directions ( a parrallel steering behaviours).
        
    def current_acc(self):
        " Current puff reduced max accel."
        cut_in=0.5
        ability_floor=0.5
        #NOTE: Turned off for now to allow easier state debugging
        return self.top_acc
        # Reduce ability linearily after cut in, down to floor
        ratio = self.puff/self.stamina
        if ratio < cut_in:
            fac = ratio*(1.-ability_floor)/cut_in + ability_floor
        else:
            fac = 1.
        return fac*self.top_acc

    def standup(self):
        """
        Check if player is prone and if so whether they can stand yet.
        """
        # Done via property now (but is it working?)
        #if self.prone > 0.:
        self.prone -= self.pitch.dt
        #    if self.prone <= 0.:
        #        self.standing=True
    
    def drop_ball(self):
        self.send(self.pitch.ball,'ball_loose')
        
class PlayerState(State.State):
    """
    Base class for Player states.
    """
    pass

class PlayerBallLoose(PlayerState):
    
    def enter(self):
        """
        NOTE: Need to look at more intelligent options than everyone going for the ball.
        """
        this=self.owner
        this.move_state = MoveState.GetLooseBall(this)

class PlayerBallCarrier(PlayerState):
    def enter(self):
        this=self.owner
        #this.move_state = MoveState.RunFreeToGoal(this)
        this.move_state = MoveState.RunUsingBlocks(this)

    def execute(self):
        # Magic numbers
        rx_project_factor = 0.6 # How much of max acc to use when projecting reciever?
        min_dist_to_sideline = 5. # How close to sidelines will be target at minimum?
        min_dist_to_endzone = 5.
        # Check for pass
        # NOTE: Checks all friends, including Blockers?
        this = self.owner
        max_range2 = this.pitch.ball.max_range_of(this)**2

        recs = [ p for p in  this.team.players.values() if p.standing and (p.pos - this.pos).mag2() < max_range2 ]
        threats = [ Threat.rx_threat(rx) for rx in recs ]
        imin = np.argmin(threats)
        best_threat = threats[imin]
        rx = recs[imin]

        my_threat = Threat.bc_threat(this)
        
        #NOTE: Doesn't take into account extra risk from pass, will lead to lots of passing.
        if my_threat > best_threat:
            # Make a pass
            # Find 'optimal' heading for the rx, weighted average of def positions using
            # the threat as the weight.
            rx_threat, scores, defenders = Threat.rx_threat(rx,full=True)
            heading=Vector(0,0)
            for d, s in zip(defenders, scores):
                # Find 'optimal' heading for this defender
                if rx.y == d.y:
                    heading_now = Vector(0,1)
                else:
                    midpoint = (d.pos + rx.pos)/2.
                    m=-1/( (rx.y-d.y)/(rx.x-d.x))
                    b = midpoint.y - m*midpoint.x
                    # Find where PB meets ez
                    # Limit target by corners, otherwise target halfway between meeting and corner.
                    ymeet = m * rx.attack_end_zone_x + b
                    if ymeet < 0:
                        ytarget=0
                    elif ymeet > rx.pitch.ysize:
                        ytarget = rx.pitch.ysize
                    else:
                        if d.y > rx.y:
                            ytarget = ymeet/2.
                        else:
                            ytarget = (ymeet + rx.pitch.ysize)/2.
                    heading_now = (Vector(rx.attack_end_zone_x,ytarget) - rx.pos).norm()
                heading += heading_now * s
            heading=heading.norm()
            # Now work out how far along heading to project as target.
            # First find TOF to Rx current location
            ball = this.pitch.ball
            tof_to_current = ball.find_time_of_flight(this, ball.find_elv_to_hit_target(this,rx.pos))
            # Project the Rx by this much time
            rx_projected_vel = (rx.vel + heading * rx.top_acc * rx_project_factor * tof_to_current).truncate(rx.top_speed)
            rx_projected_pos = rx.pos + rx_projected_vel * tof_to_current
            # Sanity check this position
            rx_projected_pos.y = Utils.bracket\
                (min_dist_to_sideline,rx_projected_pos.y,this.pitch.ysize-min_dist_to_sideline)
            rx_projected_pos.x = Utils.bracket\
                (min_dist_to_endzone,rx_projected_pos.x,this.pitch.xsize-min_dist_to_endzone)            
            # Make the throw
            this.message_handler.add(MessageHandler.Message(ball,this,'throw_made',rx_projected_pos))

class PlayerDefence(PlayerState):
    def enter(self):
        this=self.owner
        this.move_state = MoveState.TackleBallCarrierDirect(this)

class PlayerBallFlying(PlayerState):
    def enter(self):
        this=self.owner
        this.move_state = MoveState.CatchPass(this)

class DefenderDefence(PlayerState):
    def enter(self):
        this=self.owner
        this.move_state=MoveState.Defend(this)

class BlockerAttack(PlayerState):
    def enter(self):
        this=self.owner
        this.move_state=MoveState.Block(this)

class RxAttack(PlayerState):

    def enter(self):
        # Magic numbers below
        this=self.owner
        this.move_state=MoveState.FindSpace(this)


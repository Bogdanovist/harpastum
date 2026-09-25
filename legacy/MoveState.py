import State
import Steering
import MessageHandler
import pdb as debug
import math
from Vector import Vector
import scipy.optimize as opt

class MoveState(State.State):
    
    def __init__(self,owner):
        self.steering=Steering.Steering(owner)
        super(MoveState,self).__init__(owner)

    def execute(self):
        " Just resolve steering. "
        return self.steering.resolve()   

    def exit(self):
        " Turn off all steering. "
        self.steering.all_off()
        
    # Utility functions
    def calc_pbeq(self,a,d):
        if a.y == d.y:
            m=None
            b=(d.x + a.x)/2.
        elif a.x == d.x:
            m=(d.y + a.y)/2.
            b=None
        else:
            midpoint = (d.pos + a.pos)/2.
            m=-1/( (a.y-d.y)/(a.x-d.x))
            b = midpoint.y - m*midpoint.x
        return (m,b)

    def resolve_pb(self,pbeqs,pos,angle):
        """
        Find total expected gain given this PBeq, pos and angle.
        """
        this=self.owner
        # Find eq of line from pos at angle
        m = math.tan(angle)
        b = pos.y - m * pos.x
        # Find intersection point of this line and PBeq
        if pbeqs[0] == None:
            X=pbeqs[1]
            Y=m*X + b
        elif pbeqs[1] == None:
            Y=pbeqs[1]
            X=(Y-b)/m
        else:
            X = (pbeqs[1] - b)/(m - pbeqs[0])
            Y = m*X + b
        # Re-jig intersection point to be on a field boundary
        if Y < 0:
            X = -b/m
            #Y = 0
        elif Y > this.pitch.ysize:
            X = (this.pitch.ysize - b)/m
            #Y = this.pitch.ysize
        # Note the new if, we check Y then X, not one or the other.
        if X < 0:
            X=0
        elif X > this.pitch.xsize:
            X=this.pitch.xsize
        return (X-pos.x)*this.direction

    def get_contact_dist(self,a,d,angle):
        """ 
        Find projected distance we could move in a straight line, considering the supplied in contact player.
        """
        # Magic numbers
        safety_buffer=1.
        # Does this line hit the player, plus buffer?
        angle_to_defender = math.tan((d.y-a.y)/(d.x-a.x))
        diff = angle_to_defender - angle
        # s=r \theta and
        # use sin(\theta) ~ \theta for small angles
        s = diff * (d.pos-a.pos).mag()
        if s < (d.size/2. + safety_buffer):
            return (d.x - a.x)*a.direction
        else:
            m = math.tan(angle)
            b = a.y - m * a.x
            # Find Y intersection with EZ
            X = a.attack_end_zone_x
            Y = m*X + b
            # Check Y is in bounds, shift if not
            if Y < 0:
                X = -b/m
            elif Y > a.pitch.ysize:
                X = (a.pitch.ysize - b)/m
            if X < 0:
                X=0
            elif X > a.pitch.xsize:
                X=a.pitch.xsize
            return (X-a.x)*a.direction
            

class GetLooseBall(MoveState):
    def enter(self):
        this=self.owner
        self.steering.seek_on(this.pitch.ball)

class RunFreeToGoal(MoveState):
    def enter(self):
        this=self.owner
        self.steering.seek_end_zone_on(this.attack_end_zone_x,w=10)
        self.steering.avoid_defenders_on(this.opposite_team)
        self.steering.avoid_walls_on(this.pitch)

class RunUsingBlocks(MoveState):
    " Run downfield considering potential blocks."
    def enter(self):
        this=self.owner
        eps=1e-3
        if this.direction > 0:
            start_angle = -math.pi/2.+eps
            end_angle = math.pi/2.-eps
        else:
            start_angle = math.pi/2.+eps
            end_angle = 3*math.pi/2.-eps 
        self.heading = self.calc_heading(start_angle,end_angle)

    def execute(self):
        this = self.owner
        # magic number
        angle_delta = math.pi/180 * 10 # only change by at most 10 degrees each second
        a_delta = angle_delta * this.pitch.dt
        start_angle = self.heading - a_delta
        end_angle = self.heading + a_delta
        eps=1e-3
        if this.direction > 0:
            start_angle = max([-math.pi/2.+eps,start_angle])
            end_angle = min([math.pi/2.-eps,end_angle])
        else:
            start_angle = max([math.pi/2.+eps,start_angle])
            end_angle = min([3*math.pi/2.-eps,end_angle]) 
        self.heading = self.calc_heading(start_angle,end_angle)
        desired_velocity = \
            Vector( this.top_speed*math.cos(self.heading), this.top_speed*math.sin(self.heading))
        return desired_velocity - this.vel

    def calc_heading(self,start_angle,end_angle):
        this=self.owner
        # NOTE: LOTS OF OPTIM POTENTIAL!
        self.RUB_defs = [ d for d in this.opposite_team.players.values() if \
                     this.dist_to_attack_end_zone > d.dist_to_defend_end_zone ] 
        if len(self.RUB_defs) == 0:
            best_angle = math.pi/2. - math.pi/2*this.direction
            desired_velocity = Vector(this.top_speed * this.direction,0)
        else:     
            best_angle = opt.fminbound(eval_angle,start_angle,end_angle,args=(self,),xtol=0.005)
        #print(best_angle)
        return best_angle
    

    def eval_debug(self,s,e):
        nsteps=20
        da=(e-s)/(nsteps-1)
        for i in range(nsteps):
            a=s+da*i
            print(a,eval_angle(a,self))


def eval_angle(angle,self):
    " Utility function for execute."
    this=self.owner
    # Find worst dist for any defender along this angle
    worst_dist=1e10
    defs = self.RUB_defs
    for d in defs:
        if d.in_contact:
            best_dist = self.get_contact_dist(this,d,angle)
        else:
            # Find best dist offered by all potential blockers
            best_dist=0.
            for a in this.team.players.values():
                best_dist = max([self.resolve_pb( self.calc_pbeq(a,d), this.pos, angle),best_dist])
        worst_dist = min([best_dist,worst_dist])
    # -ve to turn minimiser to maximiser.
    return -worst_dist

class TackleBallCarrierDirect(MoveState):   
    def enter(self):
        this=self.owner
        self.steering.pursue_on(this.pitch.ball.carrier)
        self.steering.avoid_friends_on(this.team)

class CatchPass(MoveState):
    def enter(self):
        this=self.owner
        self.steering.arrive_at_speed_on(this.pitch.ball.target,this.pitch.ball.arrival_time)

class Defend(MoveState):
    " Target opponents near our end zone (potential recievers) "
    def execute(self):
        # Check if defensive target has been knocked over
        this=self.owner
        if self.steering._pursue_on:
            if not self.steering.pursue_target.standing:
                msg=MessageHandler.Message(this.team,this,'defensive_target_down')
                this.message_handler.add(msg)
                # This turns default no target steering back on, then resolves steering
                self.exit()
                self.enter()
        return super(Defend,self).execute()

    def get_message(self,msg):
        this=self.owner
        if msg.subject == 'defensive_target':
            target = msg.body
            self.steering.all_off()
            self.steering.pursue_on(target)
            return True
        else:
            return False

class Block(MoveState):
    def enter(self):
        this=self.owner
        self.steering.guard_on(this.pitch.ball.carrier)
        self.steering.avoid_friends_on(this.team)

    def execute(self):
        # Check if any blocking target has been knocked over
        this=self.owner
        if self.steering._block_on:
            if not self.steering.block_target.standing:
                msg=MessageHandler.Message(this.team,this,'block_target_down')
                this.message_handler.add(msg)
                # Exit then re-enter to turn back on no target behaviour
                self.exit()
                self.enter()
        # call super method to resolve steering
        return super(Block,self).execute()

    def get_message(self,msg):
        this=self.owner
        if msg.subject == 'block_target':
            block_target, block_protect = msg.body
            self.steering.block_on(block_target,block_protect)
            self.steering.guard_off()
            return True
        else:
            return False

class FindSpace(MoveState):
    
     def enter(self):
        # Magic numbers below
        this=self.owner
        self.steering.seek_end_zone_on(this.attack_end_zone_x)
        self.steering.avoid_defenders_on(this.opposite_team)
        self.steering.avoid_walls_on(this.pitch)
        self.steering.avoid_friends_on(this.team,ignore_dist=10)
        bc_range = this.pitch.ball.max_range_of(this.pitch.ball.carrier)
        self.steering.stay_in_range_on(this.pitch.ball.carrier,\
                                           max_range=bc_range*0.8,ignore_dist=bc_range*0.4)
        self.steering.avoid_end_zone_on(this.attack_end_zone_x)

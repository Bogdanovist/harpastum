from Entity import *
from Vector import *
from State import *
import Utils
import pdb as debug
import math

class Ball(Entity):
    """
    Teh Ball.
    
    Can be in one of these states:
    * setup - setting up field
    * flying - in the air
    * loose - on ground or bouncing around
    * held - in hands
    """
    def __init__(self,message_handler,pitch):
        super(Ball,self).__init__(message_handler)
        self.pitch=pitch
        self.pos = Vector(pitch.xsize/2,pitch.ysize/2.)
        self.carrier = None
        # NOTE: Assume nominal height of 2 metres if not flying, for now.
        self.z = 2.
        self.vert_vel = Vector(0,0)
        # Magic Number
        self.g = -10.
        # For when flying
        self.target = None
        self.arrival_time = None
        self.thrower = None

    def move(self):
        self.state.execute()

    def setup(self):
        self.pos = Vector(self.pitch.xsize/2,self.pitch.ysize/2.)
        self.carrier = None
        self.state = BallLoose(self)

    def get_message(self,msg):
        """
        Only message content looked at for the moment.
        """
        if msg.subject == "ball_loose":
            self.state = BallLoose(self)
        elif msg.subject == "throw_made":
            self.state = BallFlying(self,msg)
        elif msg.subject == "setup":
            self.setup()
        else:
            raise Exception("Unknown message:" + msg.subject + " recived")
    
    def scatter_ball(self,amount):
        """
        Scatters the ball by up to amount in a random direction.
        """
        self.x += np.random.random()*amount-amount/2.
        self.y += np.random.random()*amount-amount/2.
        self.x = Utils.bracket(0,self.x,self.pitch.xsize)
        self.y = Utils.bracket(0,self.y,self.pitch.ysize)

    def launch(self,elv,power,target):
        """
        Initialise throw with given angle and power from current ball position.
        """
        # 'target' is location you want the ball to pass the nominal 2m of height at
        #  
        self.carrier=None
        self.z=2. # Assume passes start 2m off the ground.
        self.vel = (target-self.pos).norm()*power*math.cos(elv)
        self.vert_vel = power*math.sin(elv)
        self.target=target
        self.arrival_time= self.pitch.game_time + (self.pos - target).mag() / self.vel.mag()

    def catch_test(self,player):
        # NOTE: Implement modifier due to nearby opponents?
        # NOTE: Implement modifier based on velocity or something (i.e. short toss easy to catch)?
        return player.catch_skill > np.random.random()*100.

    def max_range_of(self,player):
        " Returns max range this player could pass "
        return -player.throw_power**2 / self.g
    
    def find_elv_to_hit_target(self,thrower,target):
        return 0.5*math.asin( ((target - thrower.pos).mag() * (-self.g))/thrower.throw_power**2)

    def find_time_of_flight(self,thrower,elv):
        return 2*thrower.throw_power*math.sin(elv)/(-self.g)

class BallLoose(State):

    def enter(self):
        # Magic numbers
        scatter_amount=3.
        self.owner.broadcast('ball_loose')
        self.owner.scatter_ball(scatter_amount)
        self.owner.carrier = None

    def execute(self):
        """
        Check for ball pickup.
        """
        this=self.owner
        # NOTE: Players could be over-lapping and close to ball, making who ends up with it random(ish).
        # BUT, if collision between players have been resolved first, maybe this is okay?
        # NOTE: Add check of handling skill (or somesuch) to possibly fumble pickup?

        for p in this.pitch.players.values():
            dist = (p.pos - this.pos).mag2()
            if dist < p.size**2:
                this.state = BallHeld(this,p)

class BallHeld(State):

    def __init__(self,owner,carrier):
        owner.carrier=carrier
        super(BallHeld,self).__init__(owner)

    def enter(self):
        self.owner.broadcast('ball_held')

    def execute(self):
        """
        Move with ball carrier.
        """
        p = self.owner.carrier
        self.owner.pos = Vector(p.x,p.y)

class BallFlying(State):
    
    def __init__(self,owner,msg):
        self.msg = msg
        super(BallFlying,self).__init__(owner)
    
    def enter(self):
        this = self.owner
        if (self.msg.sender.pos - self.msg.body).mag() > this.max_range_of(self.msg.sender):
            elv = math.atan(1.) # 45 degrees...
        else:
            elv = this.find_elv_to_hit_target(self.msg.sender,self.msg.body)
        this.launch(elv,self.msg.sender.throw_power,self.msg.body)
        this.thrower=self.msg.sender
        this.broadcast('ball_flying')
        this.carrier=None
        
    def execute(self):
        " Iterate one flight tick "
        # Check for potential catchers
        # NOTE: Assume we can only catch if z <= 2 metres.
        # NOTE: Player heights and jumping??
        # Magic numbers
        catch_height=2.
        this = self.owner
        
        this.vert_vel += this.g * this.pitch.dt 
        znext = this.z + this.vert_vel*this.pitch.dt
        posnext = this.pos + this.vel* this.pitch.dt
        disp = posnext - this.pos

        if this.z <= catch_height:
            start = this.pos
        elif znext <= catch_height:
            # Find where ball passes catching height
            dmag = disp.mag()
            slope = (znext-this.z)/dmag
            start = this.pos + disp.norm() * ( (catch_height-this.z)/slope )
        else:
            start = None
        
        caught_it = False
        if not start == None:
            caught_it, catcher = self.check_catch(start,posnext)
            # check for catch.
            #caught_it=None
            #catchers=list()
            #for p in this.pitch.players.values():
            #    try:
            #        if (p.pos - start).mag2() < p.size**2 or (p.pos - posnext).mag2() < p.size**2 \
            #                and not p == this.thrower:
            #            catchers.append(p)
            #    except:
            #        pdb.set_trace()
            #catchers = [ p for p in this.pitch.players.values() if \
            #                 (p.pos - start).mag2() < p.size**2 or \
            #                 (p.pos - posnext).mag2() < p.size**2 and not this.thrower]
            #if len(catchers) > 1:
            #    while len(catchers) > 0:
            #        clist = [ (p.pos - start).mag2() for p in catchers ]
            #        catcher = catchers.pop(np.argmin(clist))
            #        if this.catch_test(catcher):
            #            caught_it=catcher
            #            catchers=list()   
            #elif len(catchers) == 1:
            #    if this.catch_test(catchers[0]):
            #        caught_it=catchers[0]
        
        if caught_it == False:
            this.pos = posnext
            this.z = znext
            # Check for out of bounds
            oob=False
            if this.x < 0:
                this.x = 0
                oob = True
            elif this.x > this.pitch.xsize:
                this.x = this.pitch.xsize
                oob = True
            if this.y < 0:
                this.y = 0
                oob = True
            elif this.y > this.pitch.ysize:
                this.y = this.pitch.ysize
                oob = True
            if oob:
                this.state = BallLoose(this)
                # NOTE: Simple wall like behaviour for OOB. What else to do?
            # Check for ball landing
            if this.z <= 0.:
                this.state = BallLoose(this)
        else:
            # Catch occured, change state as appropriate.
            this.state = BallHeld(this,catcher)
            # NOTE: Bit of a hack
            this.pos = catcher.pos

    def exit(self):
        this = self.owner
        this.target = None
        this.arrival_time = None
        this.thrower = None
        super(BallFlying,self).exit()

    def check_catch(self,start_pos,end_pos):
        """
        Check if anyone has caught the ball.

        Params
        ------
        start_pos, end_pos: end points along line of when the ball is at a catchable distance.
        """
        this=self.owner
        # NOTE: Add support for contested catching?
        catchers=list()
        dlist=list()
        # Tranform into ball flight co-ords
        # Transformed co-ords have origin at start pos with y-axis aligned along ball flight path.
        # Collision detection is easy in this transformed set of co-ordds (assume ball has zero size).
        diff = end_pos - start_pos
        angle = diff.angle()
        xflight = diff.mag()
        for p in this.pitch.players.values():
            if not p == this.thrower:
                ptrans = (p.pos - start_pos).rotate(-angle)
                if abs(ptrans.y) <= p.size and ptrans.x > p.x-p.size and ptrans.x < p.x+p.size:
                    print(start_pos,end_pos,p.pos,ptrans)
                    debug.set_trace()
                    catchers.append(p)
                    dlist.append(ptrans.x)
        if len(catchers) > 0:
            debug.set_trace()
            while len(catchers) > 0:
                imin = np.argmin(dlist)
                catcher = catchers.pop(imin)
                if this.catch_test(catcher):
                    return (True,catcher)
                else:
                    dlist.pop(imin)
        return (False,0)

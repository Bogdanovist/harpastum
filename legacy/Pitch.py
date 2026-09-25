from Entity import *
from Ball import * 
from Utils import *
import pdb as debug
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import json
import itertools
import random
import Helper

class Pitch(Entity):
    """
    Manager class holding both teams and the ball. Runs the game.
    """
    def __init__(self,message_handler,xsize,ysize,puff_fac=1.,damage_fac=1.):
        super(Pitch,self).__init__(message_handler)
        self.xsize=float(xsize)
        self.ysize=float(ysize)       
        self.ball=Ball(message_handler,self)
        self.moves=list()
        self.puff_fac=puff_fac
        self.damage_fac=damage_fac
        self.contacts=dict()
        self.game_time=0.
        # Add Helpers
        self.helpers=dict()
        self.helpers['AttackerDefenderPBeqs']=Helper.AttackerDefenderPBeqs()

    def register_teams(self,home,away):
        self.register(home)
        self.register(away)
        self.home=home
        self.away=away
        home.pitch=self
        away.pitch=self
        home.opposite_team=away
        away.opposite_team=home
        self.players=dict()
        for p in home.players.values():
            self.players[p.uid]=p
        for p in away.players.values():
            self.players[p.uid]=p
        # Register teams and players to the Ball
        self.ball.register(self.home)
        self.ball.register(self.away)
        for p in away.players.values():
            self.ball.register(p)
        for p in home.players.values():
            self.ball.register(p)

    def setup(self):
        self.ball.broadcast('setup',delay=-1)
        self.ball.broadcast('ball_loose',delay=-1)
        self.message_handler.clear()        
        self.ball.setup()
        self.contacts.clear()

    def run_game(self,game_length,dt=0.1,display=True):
        " Run the game "
        self.display=display
        self.dt=dt
        # Setup move storage
        self.player_header=dict()
        for p in self.home.players.values():
            self.player_header[p.uid]=make_player_dict(1,'null')
        for p in self.away.players.values():
            self.player_header[p.uid]=make_player_dict(-1,'null')            
        # Add ball to player_header
        self.player_header[self.ball.uid]=make_player_dict(0,'null')
        # Init player states using a ball state broadcast
        self.setup()
        if display:
            fig1=plt.figure()
            plt.xlim([0,self.xsize])
            plt.ylim([0,self.ysize])
            self.plots=list()
            for p in self.home.players.values():
                plot_now, = plt.plot([], [], 'ro',markersize=15)
                self.plots.append(plot_now)
            for p in self.away.players.values():
                plot_now, = plt.plot([], [], 'bo',markersize=15)
                self.plots.append(plot_now)
            plot_now, =  plt.plot([],[],'go')
            self.plots.append(plot_now)
        # Run it
        self.game_time=0.
        while self.game_time < game_length:
            # Add time FIRST, since tick() will get state to end of this interval (not start).
            self.game_time += self.dt           
            self.tick()
            if self.check_scoring():
                self.setup()
        # Dump to JSON
        jfile = "/home/matt/src/smash/games/test_header.js"
        with open(jfile,'w') as f:
            f.write(json.dumps(self.player_header))
        jfile = "/home/matt/src/smash/games/test.js"
        with open(jfile,'w') as f:
            f.write(json.dumps(self.moves))        
        if display:
            line_ani = animation.FuncAnimation(fig1,self.frame_display,self.frame_data,interval=20,blit=False,repeat=True)
            plt.show()
            
    def tick(self):
        """
        Iterate one tick.
        """
        # Process any pending messages
        self.message_handler.process()
        # Stand prone players up
        for p in self.players.values():
            p.standup()
        # Team state resolve
        self.home.state.execute()
        self.away.state.execute()
        # Move all players
        for p in self.players.values():
            p.state.execute()
            p.move()
        self.resolve_pushes()     
        self.detect_collisions()
        self.resolve_collisions()
        self.ball.move()
        # Store moves
        tick_moves=list()
        for p in self.players.values():
            add_move=make_move_dict(p.uid,p.pos.x,p.pos.y,0.,p.has_ball,int(p.standing))
            tick_moves.append(add_move)
        # Ball position
        ball_carried = self.ball.carrier != None
        add_move=make_move_dict(self.ball.uid,self.ball.pos.x,self.ball.pos.y,0,ball_carried,0)
        tick_moves.append(add_move)
        #
        self.moves.append(tick_moves)
        # Display results
        if self.display:
            self.frame_display(tick_moves)
            plt.show(block=False)
    
    def check_scoring(self):
        # Magic numbers
        end_zone_size=2.
        if self.ball.carrier == None:
            return False
        else:
            if self.ball.pos.x < end_zone_size or self.ball.pos.x > (self.xsize - end_zone_size):
                return True
            else:
                return False


    def detect_collisions(self):
        self.collisions=list()
        for this,that in itertools.combinations(self.players.values(),2):
            if not (this.standing and that.standing):
                # Prone players can be run over
                continue
            if this.in_contact and that in self.contacts[this]:
                # Don't resolve a collision for players already in contact
                continue
            else:
                if (this.pos - that.pos).mag2() - (this.size + that.size)**2 < 0:
                    # collision occured
                    collision = this, that
                    self.collisions.append(collision)

    def resolve_collisions(self):
        # NOTE: magic numbers. Where to set them?
        loser_down_diff = 0.2
        knock_down_time = 3.0 # in seconds
        loser_down_damage = 5.
        loser_up_damage = 2.
        vdiff_zero=3.
        max_post_speed = 5.
        for c in self.collisions:
            this, that = c
            if this.team == that.team:
                # NOTE: For now, ignore friendly collisions.
                continue
            else:
                # Opposing team players. Game on.
                # Find elasticity factor, runs from [0,1]
                elasticity= (this.vel.angle_factor(that.vel)+1)/2.
                this_vel_norm = this.vel.norm()
                that_vel_norm = that.vel.norm()
                # Find the direction each player will exert an extra push (directly at opponent)
                this_force_dir = (this_vel_norm - that_vel_norm).norm()
                that_force_dir = this_force_dir * -1
                # Compute initial momentum, including additional pushes along opponents bearing
                this_push=this_force_dir * this.strength * this.block_skill * random.random()
                that_push=that_force_dir * that.strength * that.block_skill * random.random()
                this_pi = this.vel * this.mass
                that_pi = that.vel * that.mass
                # Cap total push magnitude by total momentum magnitude
                p_mag = this_pi.mag() + that_pi.mag()
                push_mag = this_push.mag() + that_push.mag()
                if push_mag > p_mag:
                    this_push *= p_mag/push_mag
                    that_push *= p_mag/push_mag
                p_ini_this = this_pi + this_push
                p_ini_that = that_pi + that_push
                p_total = p_ini_this + p_ini_that
                # Whose velocity is most aligned with the total momentum? This guy has 'won' the collision.
                this_dir_fac = this.vel.angle_factor(p_total)+1
                that_dir_fac = that.vel.angle_factor(p_total)+1
                # Largest factor wins
                if this_dir_fac > that_dir_fac:
                    loser=that
                    winner=this
                    dir_fac_ratio=this_dir_fac/that_dir_fac
                else:
                    loser=this
                    winner=that
                    dir_fac_ratio=that_dir_fac/this_dir_fac
                # Determine fate of loser
                # NOTE: Chance to apply skills here
                # Damage?
                # NOTE: Very simple for now, look to uses KE lost as damage done (and use skills...)
                loser_down=compare_roll(dir_fac_ratio,loser_down_diff)
                if loser_down == -1:
                    loser.prone = knock_down_time
                    loser.health -= loser_down_damage
                else:
                    loser.health -= loser_up_damage
                # Final velocities, use elasticity
                # Find the impulse for the two extreme versions of the collision
                vfinal_inelastic = p_total/(this.mass + that.mass)
                this_inelastic_impulse = vfinal_inelastic * this.mass - p_ini_this
                that_inelastic_impulse = vfinal_inelastic * that.mass - p_ini_that
                # Elastic collision is twice impulse of an inelastic one.
                this_impulse = this_inelastic_impulse * (1.+elasticity)
                that_impulse = that_inelastic_impulse * (1.+elasticity)
                # Find final velcotiies and update
                this.vel = ((p_ini_this + this_impulse)/this.mass).truncate(max_post_speed)
                that.vel = ((p_ini_that + that_impulse)/that.mass).truncate(max_post_speed)
                # If final velocities small enough, lock players in a tussle (if both still standing)
                if loser_down != -1:
                    v_diff = (this.vel - that.vel).mag()
                    if v_diff < vdiff_zero:
                        # NOTE: IS THIS SILLY? STOPPING BOTH COMPLETELY?
                        loser.vel = Vector(0,0)
                        winner.vel = Vector(0,0)
                        self.add_contact(this,that)
    
    def resolve_pushes(self):
        # NOTE: Very simplistic, doesn't take into account angle between players, so will look weird.
        # Assumes we can have double or triple teams, but not day 2v2, so we need to prevent that elsewhere.
        # NOTE: Not losing puff for pushing, need to change that!
        # NOTE: Down chance not a comparison of skill, should be
        # Magic numbers
        down_rate = 0.2 # prob per second
        down_damage = 5.
        down_time = 3.
        clist=list()
        # Generate one push per contact player
        for p in self.players.values():
            if not p.in_contact: continue
            p.my_push = Vector( random.random() * p.strength * p.direction,0)
            p.all_pushes = [p.my_push]
            clist.append(p)
        if len(clist) == 0: return
        # Apply pushes to opponents
        for p in clist:
            # Normalise push by number of opponents
            norm = len(self.contacts[p])
            for opp in self.contacts[p]:
                opp.all_pushes.append(p.my_push / norm)
        # Sum pushes for each player and apply resultant acceleration
        for p in clist:
            acc = np.array(p.all_pushes).sum()
            temp_vel = acc * self.dt
            p.pos += temp_vel * self.dt
            # Roll for down
            # NOTE: I don't think this is correct Poisson stats!
            if random.random() < (down_rate*self.dt):
                p.prone = down_time
                p.health -= down_damage 

    def add_contact(self,a,b):
        """
        Registers that two standing players are now in a contact contest.
        """
        if not self.contacts.has_key(a):
            self.contacts[a]=set()
        self.contacts[a].add(b)
 
        if not self.contacts.has_key(b):
            self.contacts[b]=set()
        self.contacts[b].add(a)

    def remove_contact(self,a,b):
        """
        Removes the two players from the list of current contests.
        """
        self.contacts[a].discard(b)
        if len(self.contacts[a]) == 0:
            self.contacts.pop(a)
        
        self.contacts[b].discard(a)
        if len(self.contacts[b]) == 0:
            self.contacts.pop(b)            

    def remove_all_contact(self,p):
        """
        Removes the player from all contests.
        """
        # Take this player of all opponents lists
        opps = self.contacts[p]
        for opp in opps:
            self.contacts[opp].discard(p)
            if len(self.contacts[opp]) == 0:
                self.contacts.pop(opp)
        # Remove the record for this player
        self.contacts.pop(p)

    def frame_data(self):
        nticks=len(self.moves)
        iframe=0
        while iframe < nticks:
            moves=self.moves[iframe]
            iframe = iframe + 1
            yield moves

    def frame_display(self,frame_data):
        for move, p in zip(frame_data,self.plots):
            if move['state'] == 0:
                shape='v'
            else:
                shape='o'

            if self.player_header[move['uid']]['team'] == 1:
                col='r'
            elif self.player_header[move['uid']]['team'] == -1:
                col='b'
            else:
                col='g'
                shape='o'
            p.set_data(move['x'],move['y'])
            p.set_marker(shape)
            p.set_color(col)

def make_move_dict(uid,x,y,angle,have_ball,state):
    """
    Utility function to make a small dictionary to store a single move.
    """
    return dict(zip(['uid','x','y','angle','have_ball','state'],[uid,x,y,angle,have_ball,state]))

def make_player_dict(team,position):
    """
    Utility function for making player data as a small dict
    """
    return dict(zip(['team','position'],[team,position]))

import numpy as np
from Vector import Vector
import Player
import pdb as debug
import Ball

class Target(object):
    """
    Provides interface identical to players in order to use steering behaviours
    for non-player locations or players seamlessly.
    """
    def __init__(self,pos,vel):
        self.pos=pos
        self.vel=vel

class Steering(object):
    """
    Implements steering behaviours. Behaviours all return a vector indicating the direction
    that acceleration should be applied.
    """
    def __init__(self,player):
        self.priority=list()
        self.player=player
        self._seek_on=False
        self._seek_end_zone_on=False
        self._avoid_defenders_on=False
        self._avoid_walls_on=False
        self._pursue_on=False
        self._block_on=False
        self._avoid_friends_on=False
        self._zone_defend_on=False
        self._guard_on=False
        self._stay_in_range_on=False
        self._avoid_end_zone_on=False
        self._arrive_at_speed_on=False

    def seek_on(self,target,w=1.):
        self.seek_target=target
        self._seek_on=True
        self.w_seek=w

    def seek_off(self):
        self._seek_on=False

    def seek_end_zone_on(self,target,w=1.):
        self.seek_end_zone_target=target
        self._seek_end_zone_on=True
        self.w_seek_end_zone=w

    def seek_end_zone_off(self):
        self._seek_end_zone_on=False    

    def avoid_defenders_on(self,team,ignore_dist=30,panic_dist=3,w=1.):
        self._avoid_defenders_on = True
        self.w_avoid_defenders=w
        self.avoid_defenders_team=team
        self.avoid_defenders_ignore_dist=ignore_dist
        self.avoid_defenders_panic_dist=panic_dist

    def avoid_defenders_off(self):
        self._avoid_defenders_on=False

    def avoid_walls_on(self,pitch,ignore_dist=7,panic_dist=2,w=1.):
        self._avoid_walls_on = True
        self.w_avoid_walls=w
        self.avoid_walls_pitch=pitch
        self.avoid_walls_ignore_dist=7
        self.avoid_walls_panic_dist=2
        
    def avoid_walls_off(self):
        self._avoid_walls_on = False

    def pursue_on(self,target,w=1.):
        self._pursue_on = True
        self.w_pursue=w
        self.pursue_target=target
        
    def pursue_off(self):
        self._pursue_on = False

    def block_on(self,block_target,block_protect,w=1.):
        self._block_on = True
        self.w_block=w
        self.block_carrier=self.player.pitch.ball.carrier
        self.block_team=self.player.team
        self.block_target=block_target
        self.block_protect=block_protect

    def block_off(self):
        self._block_on = False

    def avoid_friends_on(self,team,ignore_dist=5,w=1.):
        self._avoid_friends_on = True
        self.w_avoid_friends=w
        self.avoid_friends_team=team
        self.avoid_friends_ignore_dist=ignore_dist

    def avoid_friends_off(self):
        self._avoid_friends_on=False

    def zone_defend_on(self,w=1.):
        self._zone_defend_on=True
        self.w_zone_defend=w
        self.zone_defend_team = self.owner.team

    def zone_defend_off(self):
        self._zone_defend_on=False

    def guard_on(self,protect,radius=5,w=1):
        self._guard_on=True
        self.w_guard=w
        self.guard_protect=protect
        self.guard_radius=radius

    def guard_off(self):
        self._guard_on=False

    def stay_in_range_on(self,bc,max_range=30,ignore_dist=20,w=1):
        self._stay_in_range_on=True
        self.w_stay_in_range=w
        self.stay_in_range_bc=bc
        self.stay_in_range_max_range=max_range
        self.stay_in_range_ignore_dist=ignore_dist

    def stay_in_range_off(self):
        self._stay_in_range_on=False

    def avoid_end_zone_on(self,ez,ignore_dist=10.,panic_dist=2.,w=1):
        self._avoid_end_zone_on=True
        self.w_avoid_end_zone=w
        self.avoid_end_zone_ez=ez
        self.avoid_end_zone_ignore_dist=ignore_dist
        self.avoid_end_zone_panic_dist=panic_dist

    def avoid_end_zone_off(self):
        self._avoid_end_zone_on=False

    def arrive_at_speed_on(self,target,time,w=1):
        self._arrive_at_speed_on=True
        self.arrive_at_speed_target=target
        self.arrive_at_speed_time=time
        self.w_arrive_at_speed=w

    def arrive_at_speed_off(self):
        self._arrive_at_speed_on=False

    def all_off(self):
        self.seek_off()
        self.seek_end_zone_off()
        self.avoid_defenders_off()
        self.avoid_walls_off()
        self.pursue_off()
        self.block_off()
        self.avoid_friends_off()
        self.zone_defend_off()
        self.guard_off()
        self.stay_in_range_off()
        self.avoid_end_zone_off()
        self.arrive_at_speed_off()

    def resolve(self):
        """
        Return combined result of all steering behaviours.
        """
        acc=Vector(0,0)
        #if type(self.player.state) == Player.RxAttack:
        #    pdb.set_trace()
        if self._avoid_defenders_on:
            acc += self.avoid_defenders() * self.w_avoid_defenders
        if self._seek_on:
            acc += self.seek() * self.w_seek
        if self._seek_end_zone_on:
            acc += self.seek_end_zone() * self.w_seek_end_zone
        if self._avoid_walls_on:
            acc += self.avoid_walls() * self.w_avoid_walls
        if self._pursue_on:
            acc += self.pursue() * self.w_pursue
        if self._block_on:
            acc += self.block() * self.w_block
        if self._avoid_friends_on:
            acc += self.avoid_friends() * self.w_avoid_friends
        if self._zone_defend_on:
            acc += self.zone_defend() * self.w_zone_defend
        if self._guard_on:
            acc += self.guard() * self.w_guard
        if self._stay_in_range_on:
            acc += self.stay_in_range() * self.w_stay_in_range
        if self._avoid_end_zone_on:
            acc += self.avoid_end_zone() * self.w_avoid_end_zone
        if self._arrive_at_speed_on:
            acc += self.arrive_at_speed() * self.w_arrive_at_speed
        return acc.truncate(self.player.top_acc)

    def seek(self):
        """
        Attempts to acc directly at target.
        """
        desired_velocity = (self.seek_target.pos-self.player.pos).norm() * self.player.top_speed
        #this=self.player
        #projected_pos = this.pos + this.vel * this.pitch.dt 
        #desired_velocity = (self.seek_target.pos - projected_pos).norm() * this.top_speed
        return (desired_velocity - self.player.vel)

    def seek_end_zone(self):
        """
        Attempts to acc directly at an end zone denoted by its x value (no y value needed).
        """
        desired_x_velocity = np.sign(self.seek_end_zone_target-self.player.x) * self.player.top_speed
        return (Vector(desired_x_velocity,0.) - self.player.vel)

    def avoid_defenders(self):
        """
        Avoid just the nearest defender by acc directly away from them.
        Ignores anyone not goalward of us, even if they are close and faster than us.
        """
        this=self.player
        ignore_dist=self.avoid_defenders_ignore_dist
        panic_dist=self.avoid_defenders_panic_dist
        #
        nearest=None
        nearest_dist2 = 1e10
        ignore_dist2=ignore_dist**2
        this_end_zone_dist = this.dist_to_attack_end_zone
        for p in self.avoid_defenders_team.players.values():
            if not p.standing: continue
            if this_end_zone_dist < p.dist_to_defend_end_zone : continue
            dist2 = (this.pos - p.pos).mag2()
            if dist2 < nearest_dist2:
                nearest=p
                nearest_dist2=dist2
        if nearest == None:
            return Vector(0,0)
        if nearest_dist2 > ignore_dist2:
            return Vector(0,0)
        else:
            # Calculate distance scaling
            dist = np.sqrt(nearest_dist2)
            if dist <= panic_dist:
                fac=1.
            else:
                fac = 1.-(dist-panic_dist)/(ignore_dist-panic_dist)
            desired_velocity = (this.pos-nearest.pos).norm()*this.top_speed*fac
            desired_acc = desired_velocity - this.vel
            # Don't permit accelerating backwards        
            if (desired_acc.x * this.direction) < 0.:
                desired_acc = Vector(0.,desired_acc.mag()*np.sign(desired_acc.y)) 
            return desired_acc

    def avoid_walls(self):
        this=self.player
        pitch=self.avoid_walls_pitch
        #
        ignore_dist=self.avoid_walls_ignore_dist
        panic_dist=self.avoid_walls_panic_dist
        #
        if this.y <= ignore_dist:
            if this.y <= panic_dist:
                desired_acc = Vector(0.,this.top_speed-this.vel.y)*2.
            else:
                fac =  1.-(this.y-panic_dist)/(ignore_dist-panic_dist)
                desired_acc = Vector(0.,(this.top_speed-this.vel.y) * fac)
        elif this.y >= (pitch.ysize-ignore_dist):
            if this.y >= (pitch.ysize-panic_dist):
                desired_acc = Vector(0.,-this.top_speed-this.vel.y)*2.
            else:
                y_diff = pitch.ysize-this.y
                fac = 1.-(y_diff-panic_dist)/(ignore_dist-panic_dist)
                desired_acc = Vector(0.,-(this.top_speed+this.vel.y) * fac)
        else:
            desired_acc = Vector(0,0)
        return desired_acc

    def pursue(self):
        " Go towards projected target position. "
        this=self.player
        # NOTE: Probably better to just assume they are running to EZ than projecting current vel? Or not?
        # NOTE: Maybe this is okay, and covering the EZ is a different behaviour. This one is good for following
        #        a recievers lead to the side.
        # How far to project? Take half distance to target and turn into travel time using their 
        # top speed. Then project their current speed for that time and seek to that position.
        
        dist = (this.pos-self.pursue_target.pos).mag()/2.
        travel_time = dist/self.pursue_target.top_speed
        # this is the 'project current velocity' version
        #projected_pos = self.pursue_target.pos + self.pursue_target.vel * travel_time
        projected_pos = self.pursue_target.pos + Vector(self.pursue_target.top_speed * this.direction * -1,0) * travel_time
        desired_velocity = (projected_pos -this.pos).norm() * this.top_speed
        return desired_velocity - this.vel
        
    def block(self):
        this = self.player

        # Want to move towards their projected position, assuming they will go straight at the 
        # player we are protecting.
        # How far to project? Take half the distance to target player and turn into travel time.
        # Project their velocity for that time and seek to that position.
        dist = (this.pos - self.block_target.pos).mag()/2.
        travel_time = dist/self.block_target.top_speed
        projected_vel = (self.block_protect.pos - self.block_target.pos).norm() * self.block_target.top_speed
        target = self.block_target.pos + projected_vel * travel_time

        desired_velocity = (target - this.pos).norm() * this.top_speed
        return (desired_velocity - this.vel)

    def avoid_friends(self):
        """
        Avoids all friends within a certain (small) radius.
        Intended as a means of preventing collisions rather than tactically spreading out.
        """
        this=self.player
        ignore_dist=self.avoid_friends_ignore_dist
        #
        acc=Vector(0,0)
        ignore2=ignore_dist**2
        a=1
        for p in self.avoid_friends_team.players.values():
            if this == p: continue
            if not p.standing:continue
            dist2 = (this.pos - p.pos).mag2()
            if dist2 < ignore2:
                acc += (this.pos-p.pos).norm()*this.top_speed*(ignore_dist-np.sqrt(dist2))/ignore_dist*2.
        return acc

    def zone_defend(self):
        """
        Try to keep equidistance between zone limits and other zoners.
        """
        # Magic numbers
        # What fraction of the distance between enemy BC and EZ to aim to sit at?
        # Higher values indicate more aggressive closer defending, lower values more defensive and further back.
        def_factor=0.5
        this = self.player

        bx=pitch.ball.x
        if this.direction > 0:
            xwant = bx * def_factor
        else:
            xwant = pitch.xsize - ( (pitch.xsize - bx) * def_factor )
        
        target=Vector(xwant,self.zone_defence_y_target)

        # Set to 'arrive' at target location with zero velocity
        diff = target-this.pos
        t_dir = diff.norm()
        dist = diff.mag()
        cur_speed = t_dir * this.vel
        stopping_distance = cur_speed**2/(2.*this.top_acc)
        if stopping_distance < dist:
            desired_velocity = t_dir * this.top_speed
        else:
            desired_velocity = t_dir * (-this.top_speed)
        
        return desired_velocity - this.vel
        
    def guard(self):
        this=self.player
        # NOTE: Can get speed up by using the Team stored nearest defender if we are guarinding the BC
        defs = [ p for p in this.opposite_team.players.values() ]
        d2 = [ (p.pos - this.pitch.ball.carrier).mag2() for p in defs]
        baddie = defs[np.argmin(d2)]
        # Find norm vector in direction of baddie from player we are protecting
        direction = (baddie.pos - self.guard_protect.pos).norm()
        # Project
        target = self.guard_protect.pos + direction * self.guard_radius
        desired_velocity = (target - this.pos).norm() * this.top_speed
        return (desired_velocity - this.vel)
        
    def stay_in_range(self):
        this=self.player
        dist=(this.pos-self.stay_in_range_bc.pos).mag()
        if dist <= self.stay_in_range_ignore_dist:
            return Vector(0,0)
        else:
            fac=(dist-self.stay_in_range_ignore_dist)\
                /(self.stay_in_range_max_range-self.stay_in_range_ignore_dist)
            desired_velocity = (self.stay_in_range_bc.pos - this.pos)*this.top_speed * fac
            return (desired_velocity - this.vel)

    def avoid_end_zone(self):
        this=self.player
        ignore_dist=self.avoid_end_zone_ignore_dist
        panic_dist=self.avoid_end_zone_panic_dist
        target = Vector(self.avoid_end_zone_ez,this.y)
        dist = (target - this.pos).mag()
        if dist <= ignore_dist:
            if dist <= panic_dist:
                fac = 1
            else:
                fac = 1.-(this.y-panic_dist)/(ignore_dist-panic_dist)
            desired_velocity = (target - this.pos).norm() * this.top_speed * fac
            ret = desired_velocity - this.vel
        else:
            ret=Vector(0,0)

        return ret

    def arrive_at_speed(self):
        this=self.player
        diff = self.arrive_at_speed_target - this.pos
        dist = diff.mag()
        time = self.arrive_at_speed_time - this.pitch.game_time
        speed = dist/time
        desired_velocity = diff.norm() * speed
        return desired_velocity - this.vel

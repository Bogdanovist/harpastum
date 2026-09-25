import numpy as np
import math

class Vector(object):
    """
    Utility class to make geometry easier.
    """
    def __init__(self,x,y):
        self.x=x
        self.y=y

    def __add__(self,that):
        return(Vector(self.x+that.x,self.y+that.y))

    def __sub__(self,that):
        return(Vector(self.x-that.x,self.y-that.y))

    def __mul__(self,that):
        """
        If vectors multiplied, silenty assumes you want the dot product.
        """
        if type(that) == Vector:
            return (self.x * that.x + self.y * that.y)
        else:
            return Vector(self.x * that, self.y * that)

    def __div__(self,that):
        """
        Only works for numerics
        """
        return Vector(self.x / that, self.y / that)

    def norm(self):
        length=self.mag()
        if length < 1e-5:
            return Vector(self.x,self.y)
        else:
            x = self.x/length
            y = self.y/length
            return Vector(x,y)

    def mag(self):
        return np.sqrt((self.x)**2 + (self.y)**2)

    def mag2(self):
        " Magnitude squared to avoid the sqrt "
        return self.x**2 + self.y**2

    def truncate(self,mag):
        """
        Ensures the magnitude of the returned vector is at most as large as the supplied.
        """
        if mag >= self.mag():
            return self
        else:
            return self.norm()*mag

    def angle_factor(self,that):
        """
        Returns a factor from the angle between the normalised vectors.
        Factor is 1 for pefect alignment and -1 for anti-alignment, 0 for right angles.
        """
        return self.norm() * that.norm()

    def rotate(self,angle):
        """
        Angle in radians.
        NOTE: This is a dumb way to do this, look up the rotation matrix when you have net access.
        """
        r = self.mag()
        theta = math.atan2(self.y,self.x)
        phi = theta+angle
        xnew = r * math.cos(phi)
        ynew = r * math.sin(phi)
        return Vector(xnew,ynew)

    def __str__(self):
        return str(self.x) + ',' + str(self.y)

    def __repr__(self):
        return str(self.x) + ',' + str(self.y)

    def angle(self):
        " Returns the angle of this vector."
        return math.atan2(self.y,self.x)

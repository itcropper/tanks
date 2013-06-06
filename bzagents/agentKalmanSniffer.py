#!/usr/bin/python -tt

# An incredibly simple agent.  All we do is find the closest enemy tank, drive
# towards it, and shoot.  Note that if friendly fire is allowed, you will very
# often kill your own tanks with this code.

#################################################################
# NOTE TO STUDENTS
# This is a starting point for you.  You will need to greatly
# modify this code if you want to do anything useful.  But this
# should help you to know how to interact with BZRC in order to
# get the information you need.
#
# After starting the bzrflag server, this is one way to start
# this code:
# python agent0.py [hostname] [port]
#
# Often this translates to something like the following (with the
# port name being printed out by the bzrflag server):
# python agent0.py localhost 49857
#################################################################

import sys
import math
import time
from random import random

from bzrc import BZRC, Command

#!/usr/bin/env python

import OpenGL
OpenGL.ERROR_CHECKING = False
import numpy
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

grid = None

def draw_grid():
    # This assumes you are using a numpy array for your grid
    width, height = grid.shape
    glRasterPos2f(-1, -1)
    glDrawPixels(width, height, GL_LUMINANCE, GL_FLOAT, grid)
    glFlush()
    glutSwapBuffers()

def update_grid(new_grid):
    global grid
    grid = new_grid

def init_window(width, height):
    global window
    global grid
    grid = numpy.zeros((width, height))
    glutInit(())
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_ALPHA | GLUT_DEPTH)
    glutInitWindowSize(width, height)
    glutInitWindowPosition(0, 0)
    window = glutCreateWindow("Grid filter")
    glutDisplayFunc(draw_grid)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    # glutMainLoop()

# vim: et sw=4 sts=4

class Agent(object):
    """Class handles all command and control logic for a teams tanks."""

    def __init__(self, bzrc):
        self.bzrc = bzrc
        self.constants = self.bzrc.get_constants()

        self.commands = []
        self.colored = []
        self.targetindex = -1

        init_window(int(self.constants["worldsize"]), int(self.constants["worldsize"]))
        
        for x in range(len(grid)):
            for y in range(len(grid[x])):
                grid[x][y] = 1

    def tick(self, time_diff):
        """Some time has passed; decide what to do next."""
        tank = self.bzrc.get_mytanks()[0]
        shots = self.bzrc.get_shots()
        self.commands = []
        
        enemytanks = self.bzrc.get_othertanks()
        #Check to see if all enemy tanks are dead and, if they are, return
        if len([t for t in enemytanks if t.status == 'alive']) == 0
            return
        #If our target is dead or uninitialized, find a live tank
        while self.targetindex < 0 or enemytanks[self.targetindex].status == 'dead':
            self.targetindex = int(random() * len(enemytanks))

        self.updateKalman(enemytanks[self.targetindex])

        #This part iteratively approaches the ideal angle at which to fire at the tank
        dtime = 0
        predictedcoord = (0, 0)
        for i in range(5):
            #For greater precision, increase the range, thereby increasing the number of predictions
            predictedcoord = self.predict(dtime)
            dtime = math.sqrt((predictedcoord[0] - tank.x)**2 + (predictedcoord[1] - tank.y)**2) / self.constants["shotspeed"]

        self.shoot(tank, coord[0], coord[1])

        #Display stuff
        self.draw_circle(tank.x + int(self.constants["worldsize"]) / 2, tank.y + int(self.constants["worldsize"]) / 2, 10, 0)
        for enemy in enemytanks:
            self.draw_x(enemy.x + int(self.constants["worldsize"]) / 2, enemy.y + int(self.constants["worldsize"]) / 2, 10, 0)
        for shot in shots:
            self.draw_x(shot.x + int(self.constants["worldsize"]) / 2, shot.y + int(self.constants["worldsize"]) / 2, 5, 0)
        draw_grid()
        #Clear the display
        while len(self.colored) > 0:
            coord = self.colored.pop()
            grid[coord[0]][coord[1]] = 1

        results = self.bzrc.do_commands(self.commands)

    def updateKalman(self, tank):
        pass

    def predict(self, time_diff):
        x = 0
        y = 0

        return (x, y)

    def shoot(self, tank, x, y):
        angleTol = math.atan2(3, math.sqrt((x - tank.x)**2 + (y - tank.y)**2))
        self.commands.append(Command(tank.index, 0, 
            1.5 * self.normalize_angle(math.atan2(y - tank.y, x - tank.x) - tank.angle), 
            abs(math.atan2(y - tank.y, x - tank.x) - tank.angle) < angleTol))

    def normalize_angle(self, angle):
        """Make any angle be between +/- pi."""
        angle -= 2 * math.pi * int (angle / (2 * math.pi))
        if angle <= -math.pi:
            angle += 2 * math.pi
        elif angle > math.pi:
            angle -= 2 * math.pi
        return angle

    def draw_circle(self, x, y, radius, color):
        for theta in drange(0, 2 * math.pi, 1.0 / (2 * radius * math.pi)):
            newx = round(x + math.cos(theta) * radius)
            newy = round(y + math.sin(theta) * radius)
            if newx > 0 and newx < len(grid) and newy > 0 and newy < len(grid):
                grid[newx][newy] = color
                if (newx, newy) not in self.colored:
                    self.colored.append((newx, newy))

    def draw_x(self, x, y, radius, color):
        for change in drange(0, radius / math.sqrt(2), 1):
            newx = round(x + change)
            newy = round(y + change)
            if newx > 0 and newx < len(grid) and newy > 0 and newy < len(grid):
                grid[newx][newy] = color
                if (newx, newy) not in self.colored:
                    self.colored.append((newx, newy))
            newx = round(x + change)
            newy = round(y - change)
            if newx > 0 and newx < len(grid) and newy > 0 and newy < len(grid):
                grid[newx][newy] = color
                if (newx, newy) not in self.colored:
                    self.colored.append((newx, newy))
            newx = round(x - change)
            newy = round(y + change)
            if newx > 0 and newx < len(grid) and newy > 0 and newy < len(grid):
                grid[newx][newy] = color
                if (newx, newy) not in self.colored:
                    self.colored.append((newx, newy))
            newx = round(x - change)
            newy = round(y - change)
            if newx > 0 and newx < len(grid) and newy > 0 and newy < len(grid):
                grid[newx][newy] = color
                if (newx, newy) not in self.colored:
                    self.colored.append((newx, newy))
        

def drange(start, stop, step):
    r = start
    while r < stop:
        yield r
        r += step

def main():
    # Process CLI arguments.
    try:
        execname, host, port = sys.argv
    except ValueError:
        execname = sys.argv[0]
        print >>sys.stderr, '%s: incorrect number of arguments' % execname
        print >>sys.stderr, 'usage: %s hostname port' % sys.argv[0]
        sys.exit(-1)

    # Connect.
    #bzrc = BZRC(host, int(port), debug=True)
    bzrc = BZRC(host, int(port))

    agent = Agent(bzrc)
    
    raw_input("Press enter to begin...")
    prev_time = time.time()

    # Run the agent
    try:
        while True:
            time_diff = time.time() - prev_time
            prev_time = time.time()
            agent.tick(time_diff)
    except KeyboardInterrupt:
        print "Exiting due to keyboard interrupt."
        bzrc.close()


if __name__ == '__main__':
    main()

# vim: et sw=4 sts=4



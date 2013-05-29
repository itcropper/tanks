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

from bzrc import BZRC, Command

#!/usr/bin/env python

import OpenGL
OpenGL.ERROR_CHECKING = False
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from numpy import zeros

grid = None
obsProp = 1.0 / 20.0

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
    grid = zeros((width, height))
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

        self.occgrid = []
        for y in range(0, int(self.constants["worldsize"])):
            self.occgrid.append([Cell() for x in range(0, int(self.constants["worldsize"]))])

        init_window(int(self.constants["worldsize"]), int(self.constants["worldsize"]))
        self.constants["chanceTrue"] =  obsProp * float(self.constants["truepositive"]) / (obsProp * float(self.constants["truepositive"]) + (1 - obsProp) * (1 - float(self.constants["truenegative"])))
        self.constants["chanceFalse"] = (1 - obsProp) * float(self.constants["truenegative"]) / ((1 - obsProp) * float(self.constants["truenegative"]) + obsProp * (1 - float(self.constants["truepositive"])))
        

    def tick(self, time_diff):
        """Some time has passed; decide what to do next."""
        # mytanks, othertanks, flags, shots = self.bzrc.get_lots_o_stuff()
        # self.mytanks = mytanks
        # self.othertanks = othertanks
        # self.flags = flags
        # self.shots = shots
        # self.enemies = [tank for tank in othertanks if tank.color !=
        #                 self.constants['team']]
        return
        self.commands = []

        # for tank in mytanks:
        #     self.attack_enemies(tank)

        # for tank in mytanks
        tank = mytanks[0]

        tempgrid = self.bzrc.get_occgrid(tank.index)
        x = tank.x
        y = tank.y
        offsetx = x + int(self.constants["worldsize"]) / 2 - len(tempgrid[1]) / 2
        if int(self.constants["worldsize"]) / 2 + x < len(tempgrid[1]) / 2:
            offsetx = 0
        if int(self.constants["worldsize"]) / 2 - x < len(tempgrid[1]) / 2:
            offsetx = int(self.constants["worldsize"]) - len(tempgrid[1])
        offsety = y + int(self.constants["worldsize"]) / 2 - len(tempgrid[1][0]) / 2
        if int(self.constants["worldsize"]) / 2 + y < len(tempgrid[1][0]) / 2:
            offsety = 0
        if int(self.constants["worldsize"]) / 2 - y < len(tempgrid[1][0]) / 2:
            offsety = int(self.constants["worldsize"]) - len(tempgrid[1][0])

        # print tank.x, tank.y, offsetx, offsety, len(tempgrid[1])

        for x in range(0, len(tempgrid[1])):
            for y in range(0, len(tempgrid[1][x])):
                grid[offsety + y][offsetx + x] = tempgrid[1][x][y]
        draw_grid()
        results = self.bzrc.do_commands(self.commands)


    def attack_enemies(self, tank):
        """Find the closest enemy and chase it, shooting as you go."""
        best_enemy = None
        best_dist = 2 * float(self.constants['worldsize'])
        for enemy in self.enemies:
            if enemy.status != 'alive':
                continue
            dist = math.sqrt((enemy.x - tank.x)**2 + (enemy.y - tank.y)**2)
            if dist < best_dist:
                best_dist = dist
                best_enemy = enemy
        if best_enemy is None:
            command = Command(tank.index, 0, 0, False)
            self.commands.append(command)
        else:
            self.move_to_position(tank, best_enemy.x, best_enemy.y)

    def move_to_position(self, tank, target_x, target_y):
        """Set command to move to given coordinates."""
        target_angle = math.atan2(target_y - tank.y,
                                  target_x - tank.x)
        relative_angle = self.normalize_angle(target_angle - tank.angle)
        command = Command(tank.index, 1, 2 * relative_angle, True)
        self.commands.append(command)

    def normalize_angle(self, angle):
        """Make any angle be between +/- pi."""
        angle -= 2 * math.pi * int (angle / (2 * math.pi))
        if angle <= -math.pi:
            angle += 2 * math.pi
        elif angle > math.pi:
            angle -= 2 * math.pi
        return angle

class Cell(object):
    def __init__(self):
        self.visited = 0
        self.occCount = 0



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

    prev_time = time.time()

    # Run the agent
    try:
        while True:
            time_diff = time.time() - prev_time
            agent.tick(time_diff)
    except KeyboardInterrupt:
        print "Exiting due to keyboard interrupt."
        bzrc.close()


if __name__ == '__main__':
    main()

# vim: et sw=4 sts=4

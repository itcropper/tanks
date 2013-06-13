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
import OpenGL
OpenGL.ERROR_CHECKING = False
import numpy as np
from numpy import linalg as LA
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from fractions import gcd

grid = None
debugDisplay = ['discretize'][0]

emptyColor = 0
obstacleColor = 1

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
    grid = np.zeros((width, height))
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

class Agent(object):
    """Class handles all command and control logic for a teams tanks."""

    def __init__(self, bzrc):
        self.bzrc = bzrc
        self.constants = self.bzrc.get_constants()
        self.constants["worldoffset"] = int(self.constants["worldsize"]) / 2
        self.obstacles = self.bzrc.get_obstacles()
        self.discretize()
        tank = self.bzrc.get_mytanks()[0]
        flag = [flag for flag in self.bzrc.get_flags() if flag.color == 'green'][0]
        start = (int((tank.y + self.constants["worldoffset"]) / self.shrinkFactor), int((tank.x + self.constants["worldoffset"]) / self.shrinkFactor))
        goal = (int((flag.y + self.constants["worldoffset"]) / self.shrinkFactor), int((flag.x + self.constants["worldoffset"]) / self.shrinkFactor))
        self.uniform_search(start, goal)
        self.commands = []

    def discretize(self):
        """This function iterates through all obstacles and finds the greatest common divisor (self.shrinkFactor) in their coordinates.
            It then creates an discrete occgrid (self.reducedGrid) where each cell in the grid represents an x by x space, where x = shrinkFactor"""
        self.shrinkFactor = int(self.constants["worldsize"])
        # Iterate through all obstacle coordinates and find their greatest common divisor
        for obstacle in self.obstacles:
            for i in range(len(obstacle)):
                coord = obstacle[i]
                nextcoord = obstacle[(i + 1) % len(obstacle)]
                self.shrinkFactor = int(min(abs(gcd(coord[0], coord[1])),
                    abs(gcd(nextcoord[0], nextcoord[1])),
                    abs(gcd(coord[0], nextcoord[0])),
                    abs(gcd(coord[1], nextcoord[1]))))
        self.reducedGrid = []
        # Establish the width/height of the grid
        sidelength = int(self.constants["worldsize"]) / self.shrinkFactor
        if debugDisplay == 'discretize':
            init_window(sidelength, sidelength)

        # Initialize the occgrid
        for y in range(sidelength):
            self.reducedGrid.append([emptyColor for x in range(sidelength)])
        if debugDisplay == 'discretize':
            for y in range(sidelength):
                for x in range(sidelength):
                    grid[x][y] = emptyColor
        # Calculate the location and area of obstacles and set their positions in the occgrid and display
        for obstacle in self.obstacles:
            start = (obstacle[2][1] + self.constants["worldoffset"]) / self.shrinkFactor, (obstacle[2][0] + self.constants["worldoffset"]) / self.shrinkFactor
            width = (obstacle[0][1] - obstacle[1][1]) / self.shrinkFactor
            height = (obstacle[1][0] - obstacle[2][0]) / self.shrinkFactor

            for y in range(int(start[1]), int(start[1] + height)):
                for x in range(int(start[0]), int(start[0] + width)):
                    if 0 <= x < sidelength and 0 <= y < sidelength:
                        if debugDisplay == 'discretize':
                            grid[x][y] = obstacleColor
                        self.reducedGrid[x][y] = obstacleColor
        print "Grid reduced by a factor of", str(self.shrinkFactor) + "!"

    def tick(self, time_diff):
        """Some time has passed; decide what to do next."""
        mytanks, othertanks, flags, shots = self.bzrc.get_lots_o_stuff()
        self.mytanks = mytanks
        self.othertanks = othertanks
        self.flags = flags
        self.shots = shots
        self.enemies = [tank for tank in othertanks if tank.color !=
                        self.constants['team']]
        draw_grid()
        self.commands = []

        results = self.bzrc.do_commands(self.commands)

    def move_to_tile(self, tank, target_x, target_y):
        """This function is used to send the tank to a certain coordinate in the occgrid. It returns false
            if the tank is not there yet, and true otherwise"""
        x = (target_x + 0.5) * self.shrinkFactor - self.constants["worldoffset"]
        y = (target_y + 0.5) * self.shrinkFactor - self.constants["worldoffset"]
        if math.sqrt((x - tank.x)**2 + (y - tank.y)**2) < self.shrinkFactor / 2:
            return true
        self.move_to_position(self, tank, x, y)
        return false

    def move_to_position(self, tank, target_x, target_y):
        """Set command to move to given coordinates."""
        target_angle = math.atan2(target_y - tank.y,
                                  target_x - tank.x)
        relative_angle = self.normalize_angle(target_angle - tank.angle)
        command = Command(tank.index, 1, 2 * relative_angle, False)
        self.commands.append(command)

    def normalize_angle(self, angle):
        """Make any angle be between +/- pi."""
        angle -= 2 * math.pi * int (angle / (2 * math.pi))
        if angle <= -math.pi:
            angle += 2 * math.pi
        elif angle > math.pi:
            angle -= 2 * math.pi
        return angle

    def uniform_search(self, start, goal):

        ToVisit = [Node(int(start[0]), int(start[1]), 0,
            math.sqrt((int(start[0]) - int(goal[0])) ** 2 + (int(start[1]) - int(goal[1])) ** 2), None)]
        Visited = {}
        curNode = None
        lastupdate = time.time()
        while len(ToVisit) > 0:
            curNode = ToVisit[0]
            lowi = 0
            for i in range(len(ToVisit)):
                if ToVisit[i].d < curNode.d:
                    lowi = i
                    curNode = ToVisit[i]
            curNode = ToVisit.pop(lowi)
            if curNode.parent != None and debugDisplay == 'discretize':
                grid[curNode.parent.x][curNode.parent.y] = .5
                grid[curNode.x][curNode.y] = .5
                # if time.time() - lastupdate > 1.0/30:
                #     lastupdate = time.time()
                #     draw_grid()
            if curNode.x == goal[0] and curNode.y == goal[1]:
                break
            for cha in [(x, y) for y in range(-1, 2) for x in range(-1, 2) if (x, y) != (0, 0)]:
                newx = curNode.x + cha[0]
                newy = curNode.y + cha[1]
                if(0 <= newx < len(self.reducedGrid) and 0 <= newy < len(self.reducedGrid[newx])):
                    if self.reducedGrid[newx][newy] == emptyColor and (curNode.x + cha[0], curNode.y + cha[1]) not in Visited:
                        newVisit = Node(curNode.x + cha[0], curNode.y + cha[1], curNode.d + math.sqrt(cha[0] ** 2 + cha[1] ** 2),
                            math.sqrt((curNode.x + cha[0] - goal[0]) ** 2 + (curNode.y + cha[1] - goal[1]) ** 2), curNode)
                        Visited[newVisit.x, newVisit.y] = newVisit
                        ToVisit.append(newVisit)
        if debugDisplay != 'none':
            print 'Path found in 1 /', int((time.time() - lastupdate)**-1), 'of a second!'
        if debugDisplay == 'discretize':
            tempNode = curNode
            while tempNode.parent != None:
                grid[tempNode.x][tempNode.y] = 0
                tempNode = tempNode.parent
            draw_grid()
        return curNode

class Node(object):
    def __init__(self, x, y, distance, heuristic, parent):
        self.x = x
        self.y = y
        self.h = heuristic
        self.d = distance
        self.parent = parent
        self.visited = False

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

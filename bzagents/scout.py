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
import random

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
            self.occgrid.append([0.0 for x in range(0, int(self.constants["worldsize"]))])
        self.visited = {}
        for x in range(int(self.constants["worldsize"])):
            for y in range(int(self.constants["worldsize"])):
                self.visited[x, y] = 0

        self.limit = 20#This is the threshold of visits before we are certain of a value !!!

        init_window(int(self.constants["worldsize"]), int(self.constants["worldsize"]))
        self.constants["chanceTrue"] =  obsProp * float(self.constants["truepositive"]) / (obsProp * float(self.constants["truepositive"]) + (1 - obsProp) * (1 - float(self.constants["truenegative"])))
        self.constants["chanceFalse"] = (1 - obsProp) * float(self.constants["truenegative"]) / ((1 - obsProp) * float(self.constants["truenegative"]) + obsProp * (1 - float(self.constants["truepositive"])))
        
        for x in range(len(grid)):
            for y in range(len(grid[x])):
                grid[x][y] = 0.5
        self.lastPath = time.time()

        mytanks = self.bzrc.get_mytanks()

        self.tankDest = [(0, 0) for tank in mytanks]
        self.tankHist = [[(0, 0) for x in range(3)] for tank in mytanks]

    def tick(self, time_diff):
        """Some time has passed; decide what to do next."""
        # self.uniform_search(self.bzrc.get_mytanks()[0])
        # return
        random.seed()
        mytanks = self.bzrc.get_mytanks()
        self.commands = []
        if len(self.visited) == 0:
            return
        for tank in mytanks:
            if (math.sqrt((self.tankDest[tank.index][0] - tank.x)**2 
                + (self.tankDest[tank.index][1] - tank.y)**2) < 20 or
                self.tankHist[tank.index][0] == self.tankHist[tank.index][2]):
                if random.randint(0, 20) == 0:
                    self.tankDest[tank.index] = (random.randint(-(int(self.constants["worldsize"]) / 2), (int(self.constants["worldsize"]) / 2)),
                        random.randint(-(int(self.constants["worldsize"]) / 2), (int(self.constants["worldsize"]) / 2)))
                else:
                    tempkey = self.visited.keys()[random.randint(0, len(self.visited.keys()) - 1)]
                    self.tankDest[tank.index] = (tempkey[0] - int(self.constants["worldsize"]) / 2, 
                        tempkey[1] - int(self.constants["worldsize"]) / 2)
            self.tankHist[tank.index].pop(0)
            self.tankHist[tank.index].append((tank.x, tank.y))
            self.move_to_position(tank, self.tankDest[tank.index][0], self.tankDest[tank.index][1])
            tempgrid = self.bzrc.get_occgrid(tank.index)

            offsetx = tempgrid[0][0] + int(self.constants["worldsize"]) / 2
            offsety = tempgrid[0][1] + int(self.constants["worldsize"]) / 2
            for x in range(0, len(tempgrid[1])):
                for y in range(0, len(tempgrid[1][x])):
                    # if (offsetx + x, offsety + y) in self.visited:
                    
                    PofSGivenO = float(self.constants["truepositive"])
                    PofSGivenNotO = 1.0 -PofSGivenO
                    PofS = grid[offsety + y][offsetx + x]
                    PofNotSGivenO = 1.0 - float(self.constants["truenegative"])
                    PofNotSGivenNotO = float(self.constants["truenegative"])
					
                    #print PofSGivenO,PofSGivenNotO,"\n",PofNotSGivenNotO, PofNotSGivenO,'\n',PofS
					
				   # return
					
                    probability = .5
					
					#print tempgrid[1][x][y]
					#return
					
                    if tempgrid[1][x][y] == 1:
                         #print "taken"
                         probability = (PofSGivenO * PofS) / ((PofSGivenO * PofS + PofNotSGivenO * (1.0 - PofS)))
                    else:
                         #print "open"
                         probability = (PofSGivenNotO * PofS) / ((PofSGivenNotO * PofS + PofNotSGivenNotO * (1.0 - PofS)))
                    grid[offsety + y][offsetx + x] = probability
                    if min(probability, 1 - probability) < 0.0001 and (offsety + x, offsety + y) in self.visited:
                         del self.visited[offsety + x, offsety + y]

        draw_grid()
        results = self.bzrc.do_commands(self.commands)

    # def uniform_search(self, start):
    #     ToVisit = [Node(int(start.x) + int(self.constants["worldsize"])  / 2, int(start.y) + int(self.constants["worldsize"]) / 2, 0, None)]
    #     Visited = {}
    #     curNode = None
    #     lastUpdate = time.time()
    #     while len(ToVisit) > 0:
    #         curNode = ToVisit[0]
    #         lowi = 0
    #         for i in range(len(ToVisit)):
    #             if ToVisit[i].d < curNode.d:
    #                 lowi = i
    #                 curNode = ToVisit[i]

    #         curNode = ToVisit.pop(lowi)
    #         grid[curNode.y][curNode.x] = 0.9 #Draw-ing
    #         if(curNode.d > 50): # Distance Limit
    #             break
    #         for cha in [(x, y) for y in range(-1, 2) for x in range(-1, 2) if (x, y) != (0, 0)]:
    #             newx = curNode.x + cha[0]
    #             newy = curNode.y + cha[1]
    #             if(newy < len(grid) and newx < len(grid[newx]) and newx >= 0 and newy >= 0):
    #                 if grid[newy][newx] != 1 and (curNode.x + cha[0], curNode.y + cha[1]) not in Visited:
    #                     newVisit = Node(curNode.x + cha[0], curNode.y + cha[1], curNode.d + math.sqrt(cha[0] ** 2 + cha[1] ** 2),
    #                     curNode)
    #                     Visited[newVisit.x, newVisit.y] = newVisit
    #                     ToVisit.append(newVisit)
    #     draw_grid()

    def move_to_position(self, tank, target_x, target_y):
        """Set command to move to given coordinates."""
        target_angle = math.atan2(target_y - tank.y,
                                  target_x - tank.x)
        relative_angle = self.normalize_angle(target_angle - tank.angle)
        speed = math.sqrt((tank.x - target_x) ** 2 + (tank.y - target_y) ** 2) / 80
        # speed = .05 if math.sqrt((tank.x - target_x) ** 2 + (tank.y - target_y) ** 2) < 20 else 1
        command = Command(tank.index, speed, 2 * relative_angle, False)
        self.commands.append(command)
        # print '(' + str(tank.x) + ', ' + str(tank.y) + ')\t' + '(' + str(target_x) + ', ' + str(target_y) + ')'

    def normalize_angle(self, angle):
        """Make any angle be between +/- pi."""
        angle -= 2 * math.pi * int (angle / (2 * math.pi))
        if angle <= -math.pi:
            angle += 2 * math.pi
        elif angle > math.pi:
            angle -= 2 * math.pi
        return angle

class Node(object):
    def __init__(self, x, y, distance, parent):
        self.x = x
        self.y = y
        self.d = distance
        self.parent = parent

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

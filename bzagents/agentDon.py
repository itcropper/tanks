#!/usr/bin/python -tt

import sys
import math
import time
from tank import Tank

from bzrc import BZRC, Command
import OpenGL
OpenGL.ERROR_CHECKING = False
import numpy as np
from numpy import matrix
from numpy import linalg as LA
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from fractions import gcd

grid = None
debugDisplay = ['', 'discretize', 'friendly', 'constants'][3]

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
        if debugDisplay == 'constants':
            print self.constants
        self.obstacles = self.bzrc.get_obstacles()
        self.discretize()
        self.commands = []
        self.ticker = 0
        self.tankpath = []
        self.last = time.time()
        self.stay_away_from = []

        mytanks, othertanks, flags, shots = self.bzrc.get_lots_o_stuff()
        self.mytanks = {tank.callsign : Tank(tank) for tank in mytanks}
        self.enemies = {tank.callsign : Tank(tank) for tank in othertanks if tank.color != self.constants["team"]}

        for tank in self.enemies.keys():
            self.enemies[tank].setSigZ(3)
            self.enemies[tank].set_world_size(self.constants["worldoffset"])

        self.colored = []

    def discretize(self):
        """This function iterates through all obstacles and finds the greatest common divisor (self.shrinkFactor) in their coordinates.
            It then creates an discrete occgrid (self.grid) where each cell in the grid represents an x by x space, where x = shrinkFactor"""
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
        self.grid = []
        # Establish the width/height of the grid
        sidelength = int(self.constants["worldsize"]) / self.shrinkFactor
        init_window(sidelength, sidelength)

        # Initialize the occgrid
        for y in range(sidelength):
            self.grid.append([emptyColor for x in range(sidelength)])
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
                        self.grid[x][y] = obstacleColor
        if debugDisplay == 'discretize':
            print "Grid reduced by a factor of", str(self.shrinkFactor) + "!"

    def updateTanks(self):
        pass


    def tick(self, time_diff):
        """Some time has passed; decide what to do next."""
        self.buddies, self.othertanks, self.flags, self.shots = self.bzrc.get_lots_o_stuff()
        self.resetGrid()
        self.commands = []
        repulse_paths = []
        if self.ticker % 1 == 0:
            repulse_paths = self.get_bullet_repulsion()

        # Let the program know what the current state of 
        # the different tanks are, like position, speed, and angle.
        for tank in self.buddies:
            self.mytanks[tank.callsign].update(tank)
        self.findRepulsionForShots(time_diff, repulse_paths)
        self.ticker += 1
        if self.ticker % 1 == 0:
            self.kalmanStuff(time_diff, int(self.constants["worldsize"]) / 2)

        # for tank in self.mytanks.keys():
        #     self.decide(self.mytanks[tank])

        results = self.bzrc.do_commands(self.commands)

    def decide(self, tank):
        """Decide upon an action to take, and take it"""
        #print tank.flag
        if tank.flag == '-' and (self.detectCarriers(tank) or self.detectEnemies(tank)):
            # Returning a flag is top priority, so this code should only run if the tank holds no flag
            return

        if len(self.tankpath) == 0:
            if tank.flag == '-':
                self.tankpath = self.search(self.convert_to_grid_tuple(tank),
                    self.convert_to_grid_tuple([flag for flag in self.bzrc.get_flags() if flag.color == 'green'][0]))
            else:
                self.tankpath = self.search(self.convert_to_grid_tuple(tank),
                    self.convert_to_grid_tuple([flag for flag in self.bzrc.get_flags() if flag.color == 'red'][0]))
        if self.move_to_tile(tank, self.tankpath[len(self.tankpath) - 1]):#!!! Detect nearest tile, move to that instead, cut list until empty
            self.tankpath.pop()

    def detectCarriers(self, tank):
        pass

    def detectEnemies(self, tank):
        pass

    def getVisibleEnemies(self, tank):
        """Checks each enemy tank for visibility from the current tank"""
        # for target in targets:

        pass

    def convert_to_grid_tuple(self, thing):
        return (int((thing.y + self.constants["worldoffset"]) / self.shrinkFactor), int((thing.x + self.constants["worldoffset"]) / self.shrinkFactor))

    def move_to_tile(self, tank, target):
        """This function is used to send the tank to a certain coordinate in the occgrid. It returns false
            if the tank is not there yet, and true otherwise"""
        x = (target[1] + 0.5) * self.shrinkFactor - self.constants["worldoffset"]
        y = (target[0] + 0.5) * self.shrinkFactor - self.constants["worldoffset"]
        # print math.sqrt((x - tank.x)**2 + (y - tank.y)**2), 'of', self.shrinkFactor / 2, '(', x, y, ')'
        if math.sqrt((x - tank.x)**2 + (y - tank.y)**2) < self.shrinkFactor * 1.8:
            return True
        self.move_to_position(tank, x, y)

        return False

    def move_to_position(self, tank, target_x, target_y):
        """Set command to move to given coordinates."""
        target_angle = math.atan2(target_y - tank.y,
                                  target_x - tank.x)
        relative_angle = self.normalize_angle(target_angle - tank.angle)
        command = Command(tank.index, 1, 2 * relative_angle, False)#math.sqrt((tank.x - target_x)**2 + (tank.y - target_y)**2) / 5
        self.commands.append(command)#max(1 - abs(relative_angle) / (math.pi / 2), 0)

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
                if(0 <= newx < len(self.grid) and 0 <= newy < len(self.grid[newx])):
                    if self.grid[newx][newy] == emptyColor and (curNode.x + cha[0], curNode.y + cha[1]) not in Visited:
                        newVisit = Node(curNode.x + cha[0], curNode.y + cha[1], curNode.d + math.sqrt(cha[0] ** 2 + cha[1] ** 2),
                            math.sqrt((curNode.x + cha[0] - goal[0]) ** 2 + (curNode.y + cha[1] - goal[1]) ** 2), curNode)
                        Visited[newVisit.x, newVisit.y] = newVisit
                        ToVisit.append(newVisit)
        if debugDisplay == 'discretize':
            print 'Path found in 1 /', int((time.time() - lastupdate)**-1), 'of a second!'
            tempNode = curNode
            while tempNode.parent != None:
                grid[tempNode.x][tempNode.y] = emptyColor
                tempNode = tempNode.parent
            draw_grid()
        return curNode

    def search(self, start, goal):
        curNode = self.uniform_search(start, goal)
        path = []
        while curNode != None:
            path.append((curNode.x, curNode.y))
            curNode = curNode.parent
        discpath = [] #This path contains only the corners, so that the tank can follow smoother straight lines
        discpath.append(path[0])
        for i in range(1, len(path) - 1):
            if path[i][0] - path[i - 1][0] != path[i + 1][0] - path[i][0] or path[i][1] - path[i - 1][1] != path[i + 1][1] - path[i][1]:
                discpath.append(path[i])
        if debugDisplay == 'discretize':
            for d in discpath:
                grid[d[0]][d[1]] = obstacleColor
            draw_grid()
        return discpath

    def isFriendlyFire(self, tank):
        a = matrix((tank.x, tank.y))
        n = matrix((float(self.constants["shotspeed"]) * math.cos(tank.angle), float(self.constants["shotspeed"]) * math.sin(tank.angle)))
        n = n / LA.norm(n)
        for mytank in [mytank for mytank in self.mytanks if mytank.index != tank.index]:
            p = matrix((mytank.x, mytank.y))
            shotdist = -((a - p).dot(n.transpose()))
            linedistance = LA.norm((a - p) + shotdist * n)
            if (0 <= shotdist < float(self.constants["shotspeed"]) and 
                linedistance < float(self.constants["tankradius"]) + float(self.constants["shotradius"]) + 2):
                return True

        return False

    def kalmanStuff(self, time_diff, worldSize):
        tempTanks = {}

        shootAt = (0,0)

        for tank in self.othertanks:
            # print tank.callsign
            tempTanks[tank.callsign] = tank

        for tank in self.mytanks.keys():
            for enemy in self.enemies.keys():
                try:
                    self.enemies[enemy].update(tempTanks[enemy])
                except KeyError:
                    continue
                #print self.enemies[enemy].x, self.enemies[enemy].y
                self.enemies[enemy].update_kalman(time_diff)
                place = self.enemies[enemy].get_target(time_diff, float(self.constants["shotspeed"]), self.mytanks[tank])
                shootAt = place
                self.draw_circle(self.enemies[enemy].x+ worldSize, self.enemies[enemy].y + worldSize, 6, .4)
                self.draw_circle(shootAt[0]+ worldSize, shootAt[1] + worldSize, 3, .4)

    
            shoot = self.mytanks[tank].shoot(shootAt[0], shootAt[1])
            self.commands.append(Command(shoot[0], shoot[1], shoot[2], shoot[3]))


    def findRepulsionForShots(self, time_diff, repulse_paths):
        for shot in repulse_paths:
            #print "SHOT FIRED!"
            for tank in self.buddies:
                self.stay_away_from.insert(0, self.repel(shot(time_diff)[0], shot(time_diff)[1], tank.x, tank.y))
                if len(self.stay_away_from) > 200:
                    self.stay_away_from.pop()


    def resetGrid(self):
        draw_grid()
        while len(self.colored) > 0:
            coord = self.colored.pop()
            grid[coord[0]][coord[1]] = 0

    def draw_circle(self, x, y, radius, color):
        for theta in drange(0, 2 * math.pi, 1.0 / (2 * radius * math.pi)):
            newy = round(x + math.cos(theta) * radius)
            newx = round(y + math.sin(theta) * radius)
            if newx > 0 and newx < len(grid) and newy > 0 and newy < len(grid):
                grid[newx][newy] = color
                if (newx, newy) not in self.colored:
                    self.colored.append((newx, newy))


    def repel(self, targetx, targety, originx, originy, radius = 20, spread = 30):
        theta = math.atan2(-(originy - targety), -(originx - targetx))
        dist = math.sqrt((originy - targety)**2 + (originx - targetx)**2)
        mag = (spread + radius - dist)/(radius + spread) * 400
        if dist > radius + spread:
            return 0, 0
        elif dist < radius:
            mag = 10000
        return mag * math.cos(theta), mag * math.sin(theta)

    def get_bullet_repulsion(self):

        bulletPredictions = []

        for shot in self.shots:
            bulletPredictions.append(lambda deltaT : (shot.x + shot.vx *deltaT, shot.y + shot.vy * deltaT))

        return bulletPredictions


class Node(object):
    def __init__(self, x, y, distance, heuristic, parent):
        self.x = x
        self.y = y
        self.h = heuristic
        self.d = distance
        self.parent = parent
        self.visited = False

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

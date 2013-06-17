#!/usr/bin/python -tt

import sys
import math
import time
from tank import Tank
from random import random

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
debugDisplay = ['', 'discretize', 'friendly', 'constants'][0]

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
        # self.dodgeShots(time_diff, repulse_paths)
        # self.ticker += 1
        # if self.ticker % 1 == 0:
        self.kalmanStuff(time_diff, int(self.constants["worldsize"]) / 2)

        for tank in [self.mytanks[tankkey] for tankkey in self.mytanks.keys()]:
            self.decide(time_diff, tank)
            # def shootAt(self, time_diff, tankkey, enemykey):
        # for tank in self.mytanks.keys():
        #     self.decide(self.mytanks[tank])

        results = self.bzrc.do_commands(self.commands)
    
    def travel_to_adjacent_cell(self, tank):
        adjCells = [(x, y) for x in range (-1, 2) for y in range(-1, 2) if (x, y) != (0, 0) and grid[x][y] != obstacleColor]
        nextCell = random.randInt(0, len(adjCells) - 1)
        self.move_to_tile(tank, (nextCell[1], nextCell[0]))
    
    def decide(self, time_diff, tank):
        """Decide upon an action to take, and take it"""
        #print tank.flag
        if not self.dodgeShots(tank):
            if tank.flag == '-' and (self.detectCarriers(time_diff, tank) or self.detectEnemies(time_diff, tank)):
                # Returning a flag is top priority, so this code should only run if the tank holds no flag
                return

            isStuck = self.mytanks[tank.callsign].historyCheck((tank.x, tank.y, tank.angle))
            if isStuck:
                try:
                    self.travel_to_adjacent_cell(self.mytanks[callsign])
                except:
                    return
            else:
                if len(self.mytanks[tank.callsign].path) == 0:
                    if tank.flag == '-':
                        flags = [flag for flag in self.bzrc.get_flags() if flag.color != self.constants["team"] and flag.poss_color != self.constants["team"]]
                        if len(flags) > 0:
                            self.mytanks[tank.callsign].path = self.search(self.convert_to_grid_tuple(tank),
                                self.convert_to_grid_tuple(sorted(flags, key=lambda inflag: math.sqrt((inflag.x - tank.x)**2 + (inflag.y - tank.y)**2))[0]))
                    else:
                        for mytank in [self.mytanks[tkey] for tkey in self.mytanks.keys() if self.mytanks[tkey].flag == '-']:
                            mytank.path = []
                        self.mytanks[tank.callsign].path = self.search(self.convert_to_grid_tuple(tank),
                            self.convert_to_grid_tuple([flag for flag in self.bzrc.get_flags() if flag.color == self.constants["team"]][0]))
                if len(self.mytanks[tank.callsign].path) > 0 and self.move_to_tile(tank, self.mytanks[tank.callsign].path[- 1]):#!!! Detect nearest tile, move to that instead, cut list until empty
                    self.mytanks[tank.callsign].path.pop()

    # This function will mimic detectEnemies, but will only chase Flag Carriers.
    def detectCarriers(self, time_diff, tank):
        visenemies = [enemy for enemy in self.getVisibleEnemies(tank) if enemy.flag != '-']
        if len(visenemies) > 0:
            self.shootAt(time_diff, tank.callsign, sorted(visenemies, key=lambda enemy: math.sqrt((enemy.x - tank.x)**2 + (enemy.y - tank.y)**2))[0].callsign)
            return True
        return False

    # This will use the occgrid to detect 'visible' tanks, then fire at them
    def detectEnemies(self, time_diff, tank):
        visenemies = self.getVisibleEnemies(tank)#[self.enemies[tankkey] for tankkey in self.enemies.keys() if math.sqrt((self.enemies[tankkey].x - tank.x)**2 + (self.enemies[tankkey].y - tank.y)**2) < 50]
        if len(visenemies) > 0:
            self.shootAt(time_diff, tank.callsign, sorted(visenemies, key=lambda enemy: math.sqrt((enemy.x - tank.x)**2 + (enemy.y - tank.y)**2))[0].callsign)
            return True
        return False

    def getVisibleEnemies(self, mytank):
        """Checks each enemy tank for visibility from the current tank"""
        # for target in targets:
        visibleEnemies = []
        for enemy in [self.enemies[tank] for tank in self.enemies.keys() if math.sqrt((self.enemies[tank].x - mytank.x)**2 + (self.enemies[tank].y - mytank.y)**2) < int(self.constants["shotrange"])]:
            vis = self.isVisible(mytank, enemy)
            # print vis, enemy.callsign
            if vis:
                visibleEnemies.append(enemy)
        return visibleEnemies

    def isVisible(self, tank, enemy):
        enemycoords = self.convert_to_grid_tuple(enemy)
        if not (0 < enemycoords[0] < len(self.grid) and 0 < enemycoords[1] < len(self.grid)):
            return False
        for coord in self.bresenham_line(self.convert_to_grid_tuple(tank), enemycoords):
            if self.grid[coord[0]][coord[1]] == obstacleColor:
                return False
        return True
        

    def bresenham_line(self, (x,y),(x2,y2)):
        """Brensenham line algorithm"""
        steep = 0
        coords = []
        dx = abs(x2 - x)
        if (x2 - x) > 0: sx = 1
        else: sx = -1
        dy = abs(y2 - y)
        if (y2 - y) > 0: sy = 1
        else: sy = -1
        if dy > dx:
            steep = 1
            x,y = y,x
            dx,dy = dy,dx
            sx,sy = sy,sx
        d = (2 * dy) - dx
        for i in range(0,dx):
            if steep: coords.append((y,x))
            else: coords.append((x,y))
            while d >= 0:
                y = y + sy
                d = d - (2 * dx)
            x = x + sx
            d = d + (2 * dy)
        coords.append((x2,y2))
        return coords

    def convert_to_grid_tuple(self, thing):
        return (int((thing.y + self.constants["worldoffset"]) / self.shrinkFactor), int((thing.x + self.constants["worldoffset"]) / self.shrinkFactor))

    def move_to_tile(self, tank, target):
        """This function is used to send the tank to a certain coordinate in the occgrid. It returns false
            if the tank is not there yet, and true otherwise"""
        x = (target[1] + 0.5) * self.shrinkFactor - self.constants["worldoffset"]
        y = (target[0] + 0.5) * self.shrinkFactor - self.constants["worldoffset"]
        # print math.sqrt((x - tank.x)**2 + (y - tank.y)**2), 'of', self.shrinkFactor / 2, '(', x, y, ')'
        if math.sqrt((x - tank.x)**2 + (y - tank.y)**2) < self.shrinkFactor / 2:
            return True
        self.move_to_position(tank, x, y)

        return False

    def move_to_position(self, tank, target_x, target_y):
        """Set command to move to given coordinates."""
        target_angle = math.atan2(target_y - tank.y,
                                  target_x - tank.x)
        relative_angle = self.normalize_angle(target_angle - tank.angle)
        command = Command(tank.index, max(1 - abs(relative_angle) / (math.pi / 2), 0), 2 * relative_angle, False)#math.sqrt((tank.x - target_x)**2 + (tank.y - target_y)**2) / 5
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
        for mytank in [self.mytanks[mytank] for mytank in self.mytanks.keys() if mytank != tank.callsign]:
            p = matrix((mytank.x, mytank.y))
            shotdist = -((a - p).dot(n.transpose()))
            linedistance = LA.norm((a - p) + shotdist * n)
            if (0 <= shotdist < float(self.constants["shotspeed"]) and 
                linedistance < float(self.constants["tankradius"]) + float(self.constants["shotradius"])):# + 2):
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
                # self.draw_circle(self.enemies[enemy].x+ worldSize, self.enemies[enemy].y + worldSize, 6, .4)
                # self.draw_circle(shootAt[0]+ worldSize, shootAt[1] + worldSize, 3, .4)

    
            # shoot = self.mytanks[tank].shoot(shootAt[0], shootAt[1])
            # self.commands.append(Command(shoot[0], shoot[1], shoot[2], shoot[3]))

    def shootAt(self, time_diff, tankkey, enemykey):
        shootAt = self.enemies[enemykey].get_target(time_diff, float(self.constants["shotspeed"]), self.mytanks[tankkey])
        shoot = self.mytanks[tankkey].shoot(shootAt[0], shootAt[1], self.getVisibleEnemies(self.mytanks[tankkey]))

        self.commands.append(Command(shoot[0], shoot[1], shoot[2], not self.isFriendlyFire(self.mytanks[tankkey]) and shoot[3]))

    def dodgeShots(self, tank):
        dist = float(self.constants["tankradius"]) + float(self.constants["shotradius"])
        dodging = False
        for shot in [myshot for myshot in self.shots if math.sqrt((myshot.x - tank.x)**2 + (myshot.y - tank.y)**2) > int(self.constants["shotspeed"]) / 2]:
            a = matrix((shot.x, shot.y))
            n = matrix((shot.vx, shot.vy))
            n = n / LA.norm(n)
            p = matrix((tank.x, tank.y))
            shotdist = -((a - p).dot(n.transpose()))
            linedistance = LA.norm((a - p) + shotdist * n)
            if linedistance < dist:
                target = matrix((0, 0)) - (a - p) + shotdist * n
                target_angle = math.atan2(target.item(0, 1), target.item(0, 0))
                relative_angle = self.normalize_angle(target_angle - tank.angle)
                command = Command(tank.index, 1, 2 * relative_angle, False)
                self.commands.append(command)

                dodging = True

        return dodging



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

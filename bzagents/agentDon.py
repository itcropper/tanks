#!/usr/bin/python -tt

import sys
import math
import time
import heapq

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

__HEURISTIC__ = 1

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
        self.tankpath = []
        self.last = time.time()

        self.grid = Grid(self.grid)
        self.op = []
        self.path = []
        heapq.heapify(self.op)
        self.cl = set()

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
        if debugDisplay == 'discretize':
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
            print "yay! ", debugDisplay

    def tick(self, time_diff):
        """Some time has passed; decide what to do next."""
        mytanks, othertanks, flags, shots = self.bzrc.get_lots_o_stuff()
        self.mytanks = mytanks
        self.othertanks = othertanks
        self.flags = flags
        self.shots = shots
        self.enemies = [tank for tank in othertanks if tank.color !=
                        self.constants['team']]

        self.commands = []
        tank = self.mytanks[0]
        if len(self.tankpath) == 0:
            if tank.flag == '-':
                self.tankpath = self.search(self.convert_to_grid_tuple(tank),
                    self.convert_to_grid_tuple([flag for flag in self.bzrc.get_flags() if flag.color == 'green'][0]))
            else:
                self.tankpath = self.search(self.convert_to_grid_tuple(tank),
                    self.convert_to_grid_tuple([flag for flag in self.bzrc.get_flags() if flag.color == 'red'][0]))
        if self.move_to_tile(tank, self.tankpath[len(self.tankpath) - 1]):#!!! Detect nearest tile, move to that instead, cut list until
            print self.tankpath.pop()

        # draw_grid()
        # if time.time() - self.last > 1:
        #     self.last = time.time()
        #     print self.isFriendlyFire(tank)
        results = self.bzrc.do_commands(self.commands)

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
        # print 'moving to ', x, y

        # position = (int((tank.x + self.constants["worldoffset"]) / self.shrinkFactor), 
        #     int((tank.y + self.constants["worldoffset"]) / self.shrinkFactor))
        
        # if math.sqrt((position[0] - target[1])**2 + (position[1] - target[0])**2) < 2:
        #     return True

        # target_angle = math.atan2(target[0] - position[1],
        #                           target[1] - position[0])
        # relative_angle = self.normalize_angle(target_angle - tank.angle)
        # command = Command(tank.index, max(1 - (relative_angle) / (math.pi / 2), 0), 2 * relative_angle, False)#math.sqrt((tank.x - target_x)**2 + (tank.y - target_y)**2) / 5
        # self.commands.append(command)
        # return False

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

    # def uniform_search(self, start, goal):

    #     ToVisit = [Node(int(start[0]), int(start[1]), 0,
    #         math.sqrt((int(start[0]) - int(goal[0])) ** 2 + (int(start[1]) - int(goal[1])) ** 2), None)]
    #     Visited = {}
    #     curNode = None
    #     lastupdate = time.time()
    #     while len(ToVisit) > 0:
    #         curNode = ToVisit[0]
    #         lowi = 0
    #         for i in range(len(ToVisit)):
    #             if ToVisit[i].d < curNode.d:
    #                 lowi = i
    #                 curNode = ToVisit[i]
    #         curNode = ToVisit.pop(lowi)
    #         if curNode.parent != None and debugDisplay == 'discretize':
    #             grid[curNode.parent.x][curNode.parent.y] = .5
    #             grid[curNode.x][curNode.y] = .5
    #             # if time.time() - lastupdate > 1.0/30:
    #             #     lastupdate = time.time()
    #             #     draw_grid()
    #         if curNode.x == goal[0] and curNode.y == goal[1]:
    #             break
    #         for cha in [(x, y) for y in range(-1, 2) for x in range(-1, 2) if (x, y) != (0, 0)]:
    #             newx = curNode.x + cha[0]
    #             newy = curNode.y + cha[1]
    #             if(0 <= newx < len(self.grid) and 0 <= newy < len(self.grid[newx])):
    #                 if self.grid[newx][newy] == emptyColor and (curNode.x + cha[0], curNode.y + cha[1]) not in Visited:
    #                     newVisit = Node(curNode.x + cha[0], curNode.y + cha[1], curNode.d + math.sqrt(cha[0] ** 2 + cha[1] ** 2),
    #                         math.sqrt((curNode.x + cha[0] - goal[0]) ** 2 + (curNode.y + cha[1] - goal[1]) ** 2), curNode)
    #                     Visited[newVisit.x, newVisit.y] = newVisit
    #                     ToVisit.append(newVisit)
    #     if debugDisplay == 'discretize':
    #         print 'Path found in 1 /', int((time.time() - lastupdate)**-1), 'of a second!'
    #         tempNode = curNode
    #         while tempNode.parent != None:
    #             grid[tempNode.x][tempNode.y] = emptyColor
    #             tempNode = tempNode.parent
    #         draw_grid()
    #     return curNode

    def search(self, start, goal):
        curNode = self.run(1)
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
        print len(discpath)
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

    def init_grid(self):

        walls = self.grid.get_grid()

        self.start = self.grid.get_cell_tuple(self.grid.start)
        self.end = self.grid.get_cell_tuple(self.grid.goal)

        #print type(self.start)

    '''
    @param cell
    @returns heuristic value H
    '''
    def get_heuristic(self, cell):

        return __HEURISTIC__ * math.sqrt((abs(cell.x - self.end.x)**2 + abs(cell.y - self.end.y)**2))

    def get_cell(self, x, y):
        """
        Returns a cell from the cells list

        @param x cell x coordinate
        @param y cell y coordinate
        @returns cell
        """

        cell = self.grid.get_cell(x,y)

        #print "Location: ", cell.x, cell.y

        return cell

    def get_adjacent_cells(self, cell):
        """
        Returns adjacent cells to a cell. Clockwise starting
        from the one on the right.

        @param cell get adjacent cells for this cell
        @returns adjacent cells list 
        """

        #vert & horizantal
        cells = []
        if cell.x + 1 < self.grid.right :
            cells.append(self.get_cell(cell.x+1, cell.y))
        if cell.y - 1 >= self.grid.bottom:
            cells.append(self.get_cell(cell.x, cell.y-1))
        if cell.x - 1 >= self.grid.left:
            cells.append(self.get_cell(cell.x-1, cell.y))
        if cell.y + 1 < self.grid.top:
            cells.append(self.get_cell(cell.x, cell.y+1))

        #diagonal
        if cell.x + 1 < self.grid.right and cell.y + 1 < self.grid.top:
            cells.append(self.get_cell(cell.x+1, cell.y+1))

        if cell.x - 1 >= self.grid.left and cell.y - 1 >= self.grid.bottom:
            cells.append(self.get_cell(cell.x-1, cell.y-1))

        if cell.x - 1 >= self.grid.left and cell.y  + 1< self.grid.top:
            cells.append(self.get_cell(cell.x-1, cell.y+1))

        if cell.x + 1 < self.grid.right and cell.y - 1 >= self.grid.bottom:
            cells.append(self.get_cell(cell.x+1, cell.y-1))

        #print cells
        return cells


    def update_cell(self, adj, cell):
        """
        Update adjacent cell

        @param adj adjacent cell to current cell
        @param cell current cell being processed
        """
        adj.cost = self.cost(cell, adj)
        adj.heuristic = self.get_heuristic(adj)
        adj.parent = cell
        adj.value = adj.heuristic + adj.cost


    def process(self):
        # add starting cell to open heap queue
        heapq.heappush(self.op, (self.start.value, self.start))
        #print "Start and Goal: ",(self.start.x, self.start.y), (self.end.x, self.end.y)
        lastupdate = time.time()
        #print self.end.x, self.end.y, "---------------------------------------------"
        
        
        while len(self.op):
            #print "GOT IN THE LOOP"
            # pop cell from heap queue 
            f, cell = heapq.heappop(self.op)
            # add cell to closed list so we don't process it twice

            #if cell.parent != None:
            #    print "set arrow from", str(cell.x) + ', ' + str(cell.y), "to ", str(cell.parent.x) + ', ' + str(cell.parent.y), "as 1"
            if time.time() - lastupdate > 0.1:
                print "plot NaN notitle"
                lastupdate = time.time()

            self.cl.add(cell)
            # if ending cell, display found path
            if cell.end:
                #print "Found Goal"
                break
            # get adjacent cells for cell
            adj_cells = self.get_adjacent_cells(cell)
            for c in adj_cells:
                #print "GOT IN NEXT LOOP"
                #print c.reachable
                if c.reachable and c not in self.cl:
                    if (c.value, c) in self.op:
                        # if adj cell in open list, check if current path is
                        # better than the one previously found for this adj
                        # cell.
                        if c.cost > self.cost(cell, c) + f:
                            self.update_cell(c, cell)

                    else:
                        self.update_cell(c, cell)
                        # add adj cell to open list
                        heapq.heappush(self.op, (c.value, c))

    def cost(self, cell1, cell2):
        cell1adj = False
        cell2adj = False
        for cha in [(x, y) for x in range(-1, 2) for y in range(-1, 2) if (x, y) != (0, 0)]:
            newx = cell1.x + cha[0] - self.occgrid[0][0]
            newy = cell1.y + cha[1] - self.occgrid[0][1]
            if self.in_range(newx, newy) and self.occgrid[1][newx][newy] == 1:
                cell1adj = True
            newx = cell2.x + cha[0] - self.occgrid[0][0]
            newy = cell2.y + cha[1] - self.occgrid[0][1]
            if self.in_range(newx, newy) and self.occgrid[1][newx][newy] == 1:
                cell2adj = True

        penalty = 1
        if not cell1adj and cell2adj:
            penalty = 1.3
        if cell1adj and cell2adj:
            penalty = 1.5
        if cell1adj and not cell2adj:
            penalty = 1.1
            
            
        return cell1.cost + penalty + math.sqrt(2) + __travel_cost__ if cell1.x != cell2.x and cell1.y !=cell2.y  else cell1.cost + penalty + __travel_cost__


    def in_range(self, x, y):
        return x >= 0 and y >= 0 and x < len(self.occgrid[1]) and y < len(self.occgrid[1][x])

    def run(self, heuristic):
        __HEURISTIC__ = heuristic
        
        self.init_grid()

        self.init_screen()
        self.refresh_screen()


        self.process()
        self.display_path()
        return self.path

class Grid():

    def __init__(self, curgrid):
        self.grid = curgrid

        self.height = len(self.grid)
        self.width  = len(self.grid[0])

        self.bottom = 0
        self.top = self.bottom + self.height

        self.left = 0
        self.right = self.left + self.width

        self.number_grid = self.grid[0]

        self.grid = []
        #!!! Get rid of this
        # self.goal =  (int(self.bzrc.get_flags()[2].x), int(self.bzrc.get_flags()[2].y))
        # self.start = (int(self.bzrc.get_mytanks()[0].x), int(self.bzrc.get_mytanks()[0].y))

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

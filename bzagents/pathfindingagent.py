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
import heapq

from bzrc import BZRC, Command

__travel_cost__ = 1

__HEURISTIC__ = 1

class Agent(object):
    """Class handles all command and control logic for a teams tanks."""

    def __init__(self, bzrc):
        self.bzrc = bzrc
        self.constants = self.bzrc.get_constants()
        self.obstacles = self.bzrc.get_obstacles()
        self.othertanks = self.bzrc.get_othertanks()
        self.occgrid = self.bzrc.get_occgrid(0)
        for tank in self.othertanks:
            for cha in [(x, y) for x in range(-2, 3) for y in range(-2, 3) if (x, y) != (0, 0)]:
                newx = int(tank.x) + cha[0] - self.occgrid[0][0]
                newy = int(tank.y) + cha[1] - self.occgrid[0][1]
                if newx >= 0 and newy >= 0 and newx < len(self.occgrid[1]) and newy < len(self.occgrid[1][x]):
                    self.occgrid[1][newx][newy] = 1
        self.grid = Grid(bzrc)
        self.op = []
        self.path = []
        heapq.heapify(self.op)
        self.cl = set()

        self.commands = []

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

        #for tank in mytanks:
        #    self.attack_enemies(tank)

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

    def init_screen(self):
        rad = int(self.constants["worldsize"]) / 2
        print "set terminal wxt size 600,600"
        print "set xrange [" + str(-rad) + ':' + str(rad) + "]"
        print "set yrange [" + str(-rad) + ':' + str(rad) + "]"
        print "unset xtics"
        print "unset ytics"
        print 'set style arrow 1 nohead lt rgb "#808080"'
        print 'set style arrow 2 nohead lw 3 lt rgb "#FF0000"'


    def refresh_screen(self):
        print "unset arrow"
        print "unset obj"
        for obstacle in self.obstacles:
            for i in range(len(obstacle)):
                print "set arrow from", str(obstacle[i][0]) + ', ' + str(obstacle[i][1]), "to", str(obstacle[(i + 1) % len(obstacle)][0]) + ', ' + str(obstacle[(i + 1) % len(obstacle)][1]), "as 1"
        for othertank in self.othertanks:
            print "set obj rect from", str(othertank.x - 3) + ', ' + str(othertank.y - 3), "to", str(othertank.x + 3) + ', ' + str(othertank.y + 3)
            #print str(tank.x) + ', ' + str(tank.y)
        print "plot NaN notitle"

    def test_occgrid(self):
        print "set terminal wxt size 600,600"
        print "set xrange [" + str(self.occgrid[0][0]) + ":" + str(len(self.occgrid[1]) + self.occgrid[0][0]) + "]"
        print "set yrange [" + str(self.occgrid[0][1]) + ":" + str(len(self.occgrid[1][0]) + self.occgrid[0][1]) + "]"
        print 'plot "-" notitle'
        for x in range(len(self.occgrid[1])):
            for y in range(len(self.occgrid[1][x])):
                if self.occgrid[1][x][y] == 1:
                    print x + self.occgrid[0][0], y + self.occgrid[0][1]
        print 'e'

    def greedy_search(self, start, goal):
        ToVisit = [Node(int(start.x), int(start.y), 0,
            math.sqrt((int(start.x) - int(goal.x)) ** 2 + (int(start.y) - int(goal.y)) ** 2), None)]
        Visited = {}
        curNode = None
        lastupdate = time.time()
        while len(ToVisit) > 0:
            curNode = ToVisit[0]
            lowi = 0
            for i in range(len(ToVisit)):
                if ToVisit[i].h < curNode.h:
                    lowi = i
                    curNode = ToVisit[i]
            curNode = ToVisit.pop(lowi)
            if curNode.parent != None:
                print 'set arrow from ', str(curNode.parent.x) + ', ' + str(curNode.parent.y), 'to', str(curNode.x) + ', ' + str(curNode.y), 'as 1'
            if curNode.x == goal.x and curNode.y == goal.y:
                break
            for cha in [(x, y) for y in range(-1, 2) for x in range(-1, 2) if (x, y) != (0, 0)]:
                newx = curNode.x + cha[0] - self.occgrid[0][0]
                newy = curNode.y + cha[1] - self.occgrid[0][1]
                if(newx < len(self.occgrid[1]) and newy < len(self.occgrid[1][newx]) and newx >= 0 and newy >= 0):
                    if self.occgrid[1][newx][newy] == 0 and (curNode.x + cha[0], curNode.y + cha[1]) not in Visited:
                        newVisit = Node(curNode.x + cha[0], curNode.y + cha[1], 0,
                            math.sqrt((curNode.x + cha[0] - goal.x) ** 2 + (curNode.y + cha[1] - goal.y) ** 2),
                            curNode)
                        Visited[newVisit.x, newVisit.y] = newVisit
                        ToVisit.append(newVisit)
            #if curNode.parent != None:
            #    print 'set arrow from ', str(curNode.parent.x) + ', ' + str(curNode.parent.y), 'to', str(curNode.x) + ', ' + str(curNode.y), 'as 1'
            if time.time() - lastupdate > 0.2:
                print 'plot NaN notitle'
                lastupdate = time.time()
        while curNode.parent != None:
                print 'set arrow from ', str(curNode.parent.x) + ', ' + str(curNode.parent.y), 'to', str(curNode.x) + ', ' + str(curNode.y), 'as 2'
                curNode = curNode.parent
        print 'plot NaN notitle'

    def uniform_search(self, start, goal):
        ToVisit = [Node(int(start.x), int(start.y), 0,
            math.sqrt((int(start.x) - int(goal.x)) ** 2 + (int(start.y) - int(goal.y)) ** 2), None)]
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
            if curNode.parent != None:
                print 'set arrow from ', str(curNode.parent.x) + ', ' + str(curNode.parent.y), 'to', str(curNode.x) + ', ' + str(curNode.y), 'as 1'
            if curNode.x == goal.x and curNode.y == goal.y:
                break
            for cha in [(x, y) for y in range(-1, 2) for x in range(-1, 2) if (x, y) != (0, 0)]:
                newx = curNode.x + cha[0] - self.occgrid[0][0]
                newy = curNode.y + cha[1] - self.occgrid[0][1]
                if(newx < len(self.occgrid[1]) and newy < len(self.occgrid[1][newx]) and newx >= 0 and newy >= 0):
                    if self.occgrid[1][newx][newy] == 0 and (curNode.x + cha[0], curNode.y + cha[1]) not in Visited:
                        newVisit = Node(curNode.x + cha[0], curNode.y + cha[1], curNode.d + math.sqrt(cha[0] ** 2 + cha[1] ** 2),
                            math.sqrt((curNode.x + cha[0] - goal.x) ** 2 + (curNode.y + cha[1] - goal.y) ** 2), curNode)
                        Visited[newVisit.x, newVisit.y] = newVisit
                        ToVisit.append(newVisit)
            if time.time() - lastupdate > 0.2:
                print 'plot NaN notitle'
                lastupdate = time.time()
        while curNode.parent != None:
                print 'set arrow from ', str(curNode.parent.x) + ', ' + str(curNode.parent.y), 'to', str(curNode.x) + ', ' + str(curNode.y), 'as 2'
                curNode = curNode.parent
        print 'plot NaN notitle'

    def iterative_search(self, start, goal):
        lastupdate = time.time()
        curNode = None
        limit = 0
        while curNode == None or curNode.x != goal.x or curNode.y != goal.y:
            limit += 1
            ToVisit = [Node(int(start.x), int(start.y), 0,
                math.sqrt((int(start.x) - int(goal.x)) ** 2 + (int(start.y) - int(goal.y)) ** 2), None)]
            Visited = {}
            self.refresh_screen()
            while len(ToVisit) > 0:
                curNode = ToVisit.pop()
                if curNode.parent != None:
                    print 'set arrow from ', str(curNode.parent.x) + ', ' + str(curNode.parent.y), 'to', str(curNode.x) + ', ' + str(curNode.y), 'as 1'
                if curNode.x == goal.x and curNode.y == goal.y:
                    break
                for cha in [(x, y) for x in range(-1, 2) for y in range(-1, 2) if (x, y) != (0, 0)]:
                    newx = curNode.x + cha[0] - self.occgrid[0][0]
                    newy = curNode.y + cha[1] - self.occgrid[0][1]
                    if(newx < len(self.occgrid[1]) and newy < len(self.occgrid[1][newx]) and newx >= 0 and newy >= 0):
                        if self.occgrid[1][newx][newy] == 0 and (curNode.x + cha[0], curNode.y + cha[1]) not in Visited and curNode.d + math.sqrt(cha[0] ** 2 + cha[1] ** 2) < limit:
                            newVisit = Node(curNode.x + cha[0], curNode.y + cha[1], curNode.d + math.sqrt(cha[0] ** 2 + cha[1] ** 2),
                                math.sqrt((curNode.x + cha[0] - goal.x) ** 2 + (curNode.y + cha[1] - goal.y) ** 2), curNode)
                            Visited[newVisit.x, newVisit.y] = newVisit
                            ToVisit.append(newVisit)
                if time.time() - lastupdate > 0.2:
                    print 'plot NaN notitle'
                    lastupdate = time.time()
        while curNode.parent != None:
                print 'set arrow from ', str(curNode.parent.x) + ', ' + str(curNode.parent.y), 'to', str(curNode.x) + ', ' + str(curNode.y), 'as 2'
                curNode = curNode.parent
        print 'plot NaN notitle'

    def depth_first(self, start, goal):
		
        first = Node(int(start.x), int(start.y), 0,
            math.sqrt((int(start.x) - int(goal.x)) ** 2 + (int(start.y) - int(goal.y)) ** 2), None)
		
        ToVisit = []
        Visited = {}
        ToVisit.append(first)
        lastupdate = time.time()
        #print goal.x, goal.y
        #print curNode.x, curNode.y, "----------------------------------------"
        while len(ToVisit) != 0:
            curNode = ToVisit.pop()
            Visited[(curNode.x, curNode.y)] = curNode
            if curNode.parent != None:
                print 'set arrow from ', str(curNode.parent.x) + ', ' + str(curNode.parent.y), 'to', str(curNode.x) + ', ' + str(curNode.y), 'as 1'
            if curNode.x == goal.x and curNode.y == goal.y:
                break
            #[1, -1],[-1, -1],[1,1],[-1, 1],[0,-1],[0,1],[1,0],[-1,0]    
            #for cha in [(x, y) for x in range(-1, 2) for y in range(-1, 2) if (x, y) != (0, 0)]:
            for cha in [[1, -1],[-1, -1],[1,1],[-1, 1],[0,-1],[0,1],[1,0],[-1,0] ]:
                newx = curNode.x + cha[0] - self.occgrid[0][0]
                newy = curNode.y + cha[1] - self.occgrid[0][1]
                if(newx < len(self.occgrid[1]) and newy < len(self.occgrid[1][newx]) and newx >= 0 and newy >= 0):
                    if self.occgrid[1][newx][newy] == 0 and not (curNode.x + cha[0], curNode.y + cha[1]) in Visited.keys():
                        newVisit = Node(curNode.x + cha[0], curNode.y + cha[1] , 0, 0, curNode)
                        
                        #curNode = newVisit
                        ToVisit.append(newVisit)
                        #break

            if time.time() - lastupdate > 0.2:
                print 'plot NaN notitle'
                lastupdate = time.time()
        while curNode.parent != None:
                print 'set arrow from ', str(curNode.parent.x) + ', ' + str(curNode.parent.y), 'to', str(curNode.x) + ', ' + str(curNode.y), 'as 2'
                curNode = curNode.parent
        print 'plot NaN notitle'

    def breadth_first(self, start, goal):
        ToVisit = [Node(int(start.x), int(start.y), 0,
            math.sqrt((int(start.x) - int(goal.x)) ** 2 + (int(start.y) - int(goal.y)) ** 2), None)]
        Visited = {}
        curNode = None
        lastupdate = time.time()
        while len(ToVisit) > 0:
            curNode = ToVisit.pop(0)
            if curNode.parent != None:
                print 'set arrow from ', str(curNode.parent.x) + ', ' + str(curNode.parent.y), 'to', str(curNode.x) + ', ' + str(curNode.y), 'as 1'
            if curNode.x == goal.x and curNode.y == goal.y:
                break
            for cha in [(x, y) for x in range(-1, 2) for y in range(-1, 2) if (x, y) != (0, 0)]:
                newx = curNode.x + cha[0] - self.occgrid[0][0]
                newy = curNode.y + cha[1] - self.occgrid[0][1]
                if(newx < len(self.occgrid[1]) and newy < len(self.occgrid[1][newx]) and newx >= 0 and newy >= 0):
                    if self.occgrid[1][newx][newy] == 0 and (curNode.x + cha[0], curNode.y + cha[1]) not in Visited:
                        newVisit = Node(curNode.x + cha[0], curNode.y + cha[1], 0, 0, curNode)
                        Visited[newVisit.x, newVisit.y] = newVisit
                        ToVisit.append(newVisit)
            if time.time() - lastupdate > 0.2:
                print 'plot NaN notitle'
                lastupdate = time.time()
        while curNode.parent != None:
                print 'set arrow from ', str(curNode.parent.x) + ', ' + str(curNode.parent.y), 'to', str(curNode.x) + ', ' + str(curNode.y), 'as 2'
                curNode = curNode.parent
        print 'plot NaN notitle'

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


    def display_path(self):
        cell = self.end
        
        while cell.parent is not self.start:
            cell = cell.parent
            self.path.append((cell.x, cell.y))
            #print 'path: cell: %d,%d' % (cell.x, cell.y)
        

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


class Cell():

    def __init__(self, x, y, reachable, value):
        self.x = x
        self.y = y
        self.value = value
        self.reachable = reachable

        self.end = False

        self.heuristic = None
        self.parent = None
        self.cost = 0


class Grid():

    def __init__(self, bzrc):
        self.bzrc = bzrc
        self.grid = self.bzrc.get_occgrid(0)

        #print self.grid

        
        self.height = len(self.grid[1])
        self.width  = len(self.grid[1][3])

        self.bottom = int(self.grid[0][0])
        self.top = self.bottom + self.height

        self.left = int(self.grid[0][0])
        self.right = self.left + self.width

        # print "Left: " , self.left
        # print 'Right: ', self.right
        # print 'Top: ', self.top
        # print 'Bottom: ', self.bottom


        #print self.height, self.width

        self.number_grid = self.grid[1:][0]

        #print self.number_grid

        self.grid = []

        self.goal =  (int(self.bzrc.get_flags()[2].x), int(self.bzrc.get_flags()[2].y))
        #print "Goal: ", self.goal, "---------------------------------------------------------"
        self.start = (int(self.bzrc.get_mytanks()[0].x), int(self.bzrc.get_mytanks()[0].y))
        # print "START: " , self.start


    '''
    @param goal: tuple(x, y)
    @returns grid of cell objects
    '''
    def get_grid(self):

        xList = []
        
        #print self.left, self.top, "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"
        
        for x in range(self.height):
            #g = raw_input(self.number_grid[y])
            yList = []

            for y in range(self.width):

                reachable = True

                if self.number_grid[x][y] == 1:
                    reachable = False
                else:
                    reachable = True
                    #print "reachable at: " + str(x) + " : " + str(y)

                cell = Cell(self.left + x, self.bottom + y, reachable, self.distance(self.left + x, self.bottom + y, self.goal))
                
                if (self.left + x, self.bottom + y) == self.goal:
                    #print "bottom: ", self.bottom, "\nleft: ", self.left, "\nX: ", x, "\nY: ", y, "\nself.left + x: ", self.left + x, "\nself.bottom + y: ", self.bottom + y
                    #s = raw_input()
                    cell.end = True

                #s = raw_input("Goal Location: " + str(x + self.left) + " : " + str(y + self.bottom) + " : " + str(self.number_grid[y][x]))

                yList.append(cell)


            xList.append(yList)

        #print len(yList), len(xList)
        
        


        self.grid = xList
        
        for tank in self.bzrc.get_othertanks():
            x = tank.x
            y = tank.y
		
            self.get_cell(x+1, y+1).reachable = False
            self.get_cell(x+1, y).reachable = False
            self.get_cell(x+1, y-1).reachable = False
            self.get_cell(x-1, y+1).reachable = False
            self.get_cell(x-1, y).reachable = False
            self.get_cell(x-1, y-1).reachable = False
            self.get_cell(x, y+1).reachable = False
            self.get_cell(x, y-1).reachable = False
            self.get_cell(x, y).reachable = False
            
            #print x, y, tank.color
            #s = raw_input()

        return y
                
    def distance(self, x, y, goal):
        return math.sqrt((abs(x - goal[0])**2 + (abs(y - goal[1])**2)))

    def get_cell(self, x, y):

        x = int(x + self.right)
        y = int(y + self.top)

        #print "Get Cell: ", x, y

        try:
            return self.grid[x][y]
        except(IndexError):
            print "Max is: " + str(len(self.grid)) + ", " + str(len(self.grid[0]))
            print "Error on: Index: " + str(x) + ", " + str(y)
            sys.exit(0)

    def get_cell_tuple(self, xy):
        x = int(xy[0] + self.right)
        y = int(xy[1] + self.top)

        return self.grid[x][y]

    def get_cell_by_cell(self, c):
        return self.grid[int(c[0])][int(c[1])]

                


#grid = Grid(38943)

#print grid.get_grid()

#400 X 400
    
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

    start = bzrc.get_mytanks()[0]
    goal = next(flag for flag in bzrc.get_flags() if flag.color == 'green')

    agent.init_screen()
    agent.refresh_screen()

    #agent.test_occgrid()
    #agent.uniform_search(start, goal)
    #agent.greedy_search(start, goal)
    #agent.depth_first(start, goal)
    #agent.breadth_first(start, goal)
    #agent.iterative_search(start, goal)
    path = agent.run(1)
    for i in range(len(path)):
        if i < len(path) - 1:
            print "set arrow from", str(path[i][0]) + ', ' + str(path[i][1]), "to ", str(path[i + 1][0]) + ', ' + str(path[i + 1][1]), "as 2"
    print "plot NaN notitle"
    print time.time() - prev_time
    return

    
    

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

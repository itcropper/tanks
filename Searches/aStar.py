
import heapq
import sys
from datetime import datetime
from occGrid import Grid
import math

sys.path.insert(0, '/home/ian/Dropbox/School/Spring 2013/AI/tanks/bzagents')

from bzrc import BZRC

__FILE_NAME__ = "path.gpi"

__travel_cost__ = 5

__HEURISTIC__ = 1

class AStar(object):

    def __init__(self):
        self.op = []
        heapq.heapify(self.op)
        self.cl = set()
        localhost = "localhost"
        self.path = []
        self.grid = Grid(port=int(33172))
        self.bz = BZRC(host="localhost", port=int(33172))
        self.obstacles = self.bz.get_obstacles()
        self.othertanks = self.bz.get_othertanks()

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
        adj.cost = cell.cost + __travel_cost__
        adj.heuristic = self.get_heuristic(adj)
        adj.parent = cell
        adj.value = adj.heuristic + adj.cost


    def process(self):
        # add starting cell to open heap queue
        heapq.heappush(self.op, (self.start.value, self.start))
        #print "Start and Goal: ",(self.start.x, self.start.y), (self.end.x, self.end.y)

        while len(self.op):
            #print "GOT IN THE LOOP"
            # pop cell from heap queue 
            f, cell = heapq.heappop(self.op)
            # add cell to closed list so we don't process it twice

            #print cell.end

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
                        if c.cost < cell.cost + __travel_cost__:
                            self.update_cell(c, cell)

                    else:
                        self.update_cell(c, cell)
                        # add adj cell to open list
                        heapq.heappush(self.op, (c.value, c))


    def init_screen(self):
        rad = int(self.grid.width) / 2
        print "set terminal wxt size 600,600"
        print "set xrange [" + str(-rad) + ':' + str(rad) + "]"
        print "set yrange [" + str(-rad) + ':' + str(rad) + "]"
        print "unset xtics"
        print "unset ytics"
        print "set style arrow 1 nohead"


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

    def run(self, heuristic):
        __HEURISTIC__ = heuristic
        
        self.init_grid()

        self.init_screen()
        self.refresh_screen()


        self.process()
        self.display_path()
        return self.path



def run(heuristic):
    __HEURISTIC__ = heuristic
    a = AStar()
    a.run()
    return a.path
    #print a.path

'''
2*: 0:00:32.264834
4*: 0:02:16.979825
1*: 0:01:30.079064
'''


if __name__ == "__main__":
    a = AStar()
    #then = datetime.now()
    path = a.run(1.5)
    for i in range(len(path)):
        if i < len(path) - 1:
            print "set arrow from", str(path[i][0]) + ', ' + str(path[i][1]), "to", str(path[i + 1][0]) + ', ' + str(path[i+1][1]), "as 2"
    print "plot NaN notitle"
    #print datetime.now() - then


import heapq
from occGrid import Grid

__travel_cost__ = 5

class AStar(object):

    def __init__(self):
        self.op = []
        heapq.heapify(self.op)
        self.cl = set()
        self.gridHeight = 6
        self.gridWidth = 6
        self.path = []
        self.grid = Grid(port=53560)
        self.goal = (100, 0)

    def init_grid(self):

        walls = self.grid.get_grid(self.goal)

        self.start = self.grid.get_cell(-200, 0)
        self.end = self.grid.get_cell(100, 0)

    def get_heuristic(self, cell):
        """
        Compute the heuristic value H for a cell: distance between
        this cell and the ending cell multiply by 10.

        @param cell
        @returns heuristic value H
        """
        return 10 * (abs(cell.x - self.goal[0]) + abs(cell.y - self.goal[1]))

    def get_cell(self, x, y):
        """
        Returns a cell from the cells list

        @param x cell x coordinate
        @param y cell y coordinate
        @returns cell
        """
        return self.grid.get_cell(x,y)

    def get_adjacent_cells(self, cell):
        """
        Returns adjacent cells to a cell. Clockwise starting
        from the one on the right.

        @param cell get adjacent cells for this cell
        @returns adjacent cells list 
        """
        cells = []
        if cell.x < self.grid.top-1:
            cells.append(self.get_cell(cell.x+1, cell.y))
        if cell.y > 0:
            cells.append(self.get_cell(cell.x, cell.y-1))
        if cell.x > 0:
            cells.append(self.get_cell(cell.x-1, cell.y))
        if cell.y < self.grid.top-1:
            cells.append(self.get_cell(cell.x, cell.y+1))
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
        adj.value = cell.value + __travel_cost__
        adj.heuristic = self.get_heuristic(adj)
        adj.parent = cell
        adj.value = adj.heuristic + adj.g


    def process(self):
        # add starting cell to open heap queue
        heapq.heappush(self.op, (self.start.value, self.start))
        while len(self.op):
            # pop cell from heap queue 
            f, cell = heapq.heappop(self.op)
            # add cell to closed list so we don't process it twice
            self.cl.add(cell)
            # if ending cell, display found path
            if cell is self.end:
                self.display_path()
                break
            # get adjacent cells for cell
            adj_cells = self.get_adjacent_cells(cell)
            for c in adj_cells:
                if c.reachable and c not in self.cl:
                    if (c.f, c) in self.op:
                        # if adj cell in open list, check if current path is
                        # better than the one previously found for this adj
                        # cell.
                        if c.g > cell.g + 10:
                            self.update_cell(c, cell)
                    else:
                        self.update_cell(c, cell)
                        # add adj cell to open list
                        heapq.heappush(self.op, (c.f, c))

    def run():
        self.init_grid()
        self.process()



if __name__ == "__main__":
    a = AStar()
    a.init_grid()
    a.process()
    print a.path
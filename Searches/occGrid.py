import sys
import math

sys.path.insert(0, '/home/ian/Dropbox/School/Spring 2013/AI/tanks/bzagents')

from bzrc import BZRC


class Cell():

	def __init__(self, x, y, reachable, value):
		self.x = x
		self.y = y
		self.value = value
		self.reachable = reachable

		self.heuristic = None
		self.parent = None


class Grid():

	def __init__(self, port):

		self.bzrc = BZRC("localhost", int(port))
		self.grid = self.bzrc.get_occgrid(0)
		self.top = -1 * int(self.grid[0][0])
		self.bottom = int(self.grid[0][1])

		self.number_grid = self.grid[1:][0]
		self.grid = []


	'''
	@param goal: tuple(x, y)
	@returns grid of cell objects
	'''
	def get_grid(self, goal):
		yList = []
		
		for y in range(len(self.number_grid)):

			xList = []

			for x in range(len(self.number_grid[y])):
				if self.number_grid[y][x] == 1:
					reachable = False
				else:
					reachable = True

				xList.append(Cell(x, y, reachable, self.distance(x, y, goal)))


			yList.append(xList)

		print len(yList), len(xList)

		self.grid = yList

		return y
				
	def distance(self, x, y, goal):
		return math.sqrt((abs(x - goal[0])**2 + (abs(y - goal[1])**2)))

	def get_cell(self, x, y):
		print "Getting Cell: ", x + 200, y + 200
		return self.grid[200 + x - 1][y + 200 - 1]

				


#grid = Grid(38943)

#print grid.get_grid()

#400 X 400


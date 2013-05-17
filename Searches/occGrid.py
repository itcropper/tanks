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

		self.end = False

		self.heuristic = None
		self.parent = None
		self.cost = 0


class Grid():

	def __init__(self, port):

		self.bzrc = BZRC("localhost", int(port))
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
		# print "Goal: ", self.goal
		self.start = (int(self.bzrc.get_mytanks()[0].x), int(self.bzrc.get_mytanks()[0].y))
		# print "START: " , self.start


	'''
	@param goal: tuple(x, y)
	@returns grid of cell objects
	'''
	def get_grid(self):

		xList = []
		
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

				cell = Cell(self.left + x, self.bottom + y, reachable, self.distance(self.left + x, self.right + y, self.goal))
				
				if (self.left + x, self.top + y) == self.goal:
					cell.end = True

				#s = raw_input("Goal Location: " + str(x + self.left) + " : " + str(y + self.bottom) + " : " + str(self.number_grid[y][x]))

				yList.append(cell)


			xList.append(yList)

		#print len(yList), len(xList)

		self.grid = xList

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


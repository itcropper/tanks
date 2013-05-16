
import sys
import math
import time

from bzrc import BZRC, Command

port = raw_input("Port?")
print port

bzrc = BZRC('127.0.0.1', int(port))

f = open("grid.txt", 'w')


grid = bzrc.get_occgrid(0)

f.write(str(grid[0][1] + grid[0][2]))


for line in grid[1]:
	l = ''
	for s in line:
		l += str(s)
	f.write(l + "\n")
#f.write(bzrc.get_occgrid(0))
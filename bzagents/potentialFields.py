#!/usr/bin/env python
'''This is a demo on how to use Gnuplot for potential fields.  We've
intentionally avoided "giving it all away."
'''

from __future__ import division
from itertools import cycle

from bzrc import BZRC
from Gnuplot import GnuplotProcess
import sys

__bzrc__ = None


# This is stolen from numpy.  If numpy is installed, you don't
# need this:
def linspace(start, stop, num=200, endpoint=True, retstep=False):
    """Return evenly spaced numbers.

    Return num evenly spaced samples from start to stop.  If
    endpoint is True, the last sample is stop. If retstep is
    True then return the step value used.
    """
    num = int(num)
    if num <= 0:
        return []
    if endpoint:
        if num == 1:
            return [float(start)]
        step = (stop-start)/float((num-1))
        y = [x * step + start for x in xrange(0, num - 1)]
        y.append(stop)
    else:
        step = (stop-start)/float(num)
        y = [x * step + start for x in xrange(0, num)]
    if retstep:
        return y, step
    else:
        return y
        



########################################################################
# Constants

# Output file:
FILENAME = 'fields.gpi'
# Size of the world (one of the "constants" in bzflag):
WORLDSIZE = 1000
# How many samples to take alplotToFileong each dimension:
SAMPLES = 50
# Change spacing by changing the relative length of the vectors.  It looks
# like scaling by 0.75 is pretty good, but this is adjustable:
VEC_LEN = 0.75 * WORLDSIZE / SAMPLES
# Animation parameters:
ANIMATION_MIN = 0
ANIMATION_MAX = 500
ANIMATION_FRAMES = 50



class Plot():
	
	def __init__(self):
		pass

	########################################################################
	# Field and Obstacle Definitions

	def generate_field_function(self, scale):
		def function(x, y):
			'''User-defined field function.'''
			sqnorm = (x**2 + y**2)
			if sqnorm == 0.0:
				return 0, 0
			else:
				return x*scale/sqnorm, y*scale/sqnorm
		return function

					



	########################################################################
	# Helper Functions



	def gpi_point(self, x, y, vec_x, vec_y):
		'''Create the centered gpi data point (4-tuple) for a position and
		vector.  The vectors are expected to be less than 1 in magnitude,
		and larger values will be scaled down.'''
		r = (vec_x ** 2 + vec_y ** 2) ** 0.5
		if r > 1:
			vec_x /= r
			vec_y /= r
		return (x - vec_x * VEC_LEN / 2, y - vec_y * VEC_LEN / 2,
				vec_x * VEC_LEN, vec_y * VEC_LEN)

	def gnuplot_header(self, minimum, maximum):
		'''Return a string that has all of the gnuplot sets and unsets.'''
		s = ''
		s += 'set xrange [%s: %s]\n' % (minimum, maximum)
		s += 'set yrange [%s: %s]\n' % (minimum, maximum)
		# The key is just clutter.  Get rid of it:
		s += 'unset key\n'
		# Make sure the figure is square since the world is square:
		s += 'set size square\n'
		# Add a pretty title (optional):
		#s += "set title 'Potential Fields'\n"
		return s

	def draw_line(self, p1, p2):
		'''Return a string to tell Gnuplot to draw a line from point p1 to
		point p2 in the form of a set command.'''
		x1, y1 = p1
		x2, y2 = p2
		return 'set arrow from %s, %s to %s, %s nohead lt 3\n' % (x1, y1, x2, y2)

	def draw_obstacles(self, obstacles):
		'''Return a string which tells Gnuplot to draw all of the obstacles.'''
		s = 'unset arrow\n'

		for obs in obstacles:
			last_point = obs[0]
			for cur_point in obs[1:]:
				s += self.draw_line(last_point, cur_point)
				last_point = cur_point
			s += self.draw_line(last_point, obs[0])
		return s
		
	def drawSquares(self, x, y):
		arrow = "set arrow from "
		end = " nohead lt 2"

		left = arrow + str(x - 10) + ", "+ str(y - 10) + " to " + str(x - 10) + ", "+ str(y + 10) + end + "\n"
		top = arrow + str(x - 10) + ", "+ str(y + 10) + " to " + str(x + 10) + ", "+ str(y + 10) + end + "\n"
		right = arrow + str(x + 10) + ", "+ str(y + 10) + " to " + str(x + 10) + ", "+ str(y - 10) + end + "\n"
		bottom = arrow + str(x + 10) + ", "+ str(y - 10) + " to " + str(x - 10) + ", "+ str(y - 10) + end + "\n"

		return left + top + right + bottom + "\n"

	def drawExes(self, x, y):
		arrow = "set arrow from "
		end = " nohead lt 4"

		left = arrow + str(x - 10) + ", "+ str(y - 10) + " to " + str(x + 10) + ", "+ str(y + 10) + end + "\n"
		top = arrow + str(x - 10) + ", "+ str(y + 10) + " to " + str(x + 10) + ", "+ str(y - 10) + end + "\n"

		return left + top + "\n"
		
	def draw_points(self, points, element):
		
		'''
		set arrow from 0.0, 0.0 to 0.0, 20.0 nohead lt 4
		set arrow from 0.0, 20.0 to 20.0, 20.0 nohead lt 4
		set arrow from 20.0, 20.0 to 20.0, 0.0 nohead lt 4
		set arrow from 20.0, 0.0 to 0.0, 0.0 nohead lt 4
		'''
		
		s = ''

		for p in points:
			if element == "tanks": #tanks are squares
				s += self.drawSquares(p.x, p.y)
				
			elif element == "flags": #flags are circles
				s += self.drawExes(p.x, p.y)

		return s
		
		
	def attracitve_planes(self, attratants):
		pass
		
	

	def plot_field(self, function):
		'''Return a Gnuplot command to plot a field.'''
		s = "plot '-' with vectors head\n"

		separation = WORLDSIZE / SAMPLES
		end = WORLDSIZE / 2 - separation / 2
		start = -end
		#---------------------------------------------------------Here is where you need to change stuff up

		points = ((x, y) for x in linspace(start, end, SAMPLES)
					for y in linspace(start, end, SAMPLES))

		for x, y in points:
			f_x, f_y = function(x + 50, y + 50)
			plotvalues = self.gpi_point(x, y, f_x, f_y)
			if plotvalues is not None:
				x1, y1, x2, y2 = plotvalues
				s += '%s %s %s %s\n' % (x1, y1, x2, y2)
		s += 'e\n'
		return s


	def plotToFile(self, obstacles):

	########################################################################
	# Plot the potential fields to a file

		outfile = open(FILENAME, 'w')
		print >>outfile, self.gnuplot_header(-WORLDSIZE / 2, WORLDSIZE / 2)
		print >>outfile, self.draw_obstacles(obstacles)

		
	def appendToFile(self, flags, tanks):

		#print "appending to file"
		
		outfile = open(FILENAME, 'a')
		print >>outfile, self.draw_points(flags, "flags")
		print >>outfile, self.draw_points(tanks, "tanks")

		field_function = self.generate_field_function(100)
		print >>outfile, self.plot_field(field_function)


	########################################################################
	# Animate a changing field, if the Python Gnuplot library is present


	def animate(self, obstacles):

		forward_list = list(linspace(ANIMATION_MIN, ANIMATION_MAX, ANIMATION_FRAMES/2))
		backward_list = list(linspace(ANIMATION_MAX, ANIMATION_MIN, ANIMATION_FRAMES/2))

		#print forward_list

		anim_points = forward_list + backward_list

		gp = GnuplotProcess(persist=False)
		gp.write(self.gnuplot_header(-WORLDSIZE / 4, WORLDSIZE / 4))
		gp.write(self.draw_obstacles(obstacles))
		#gp.write(self.draw_points(tanks, "tanks"))

		#print "getting here alright:"

		#for scale in cycle(anim_points):
		#	field_function = self.generate_field_function(scale)

		#	gp.write(self.plot_field(field_function))



class main():
	
	def __init__(self):
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
		__bzrc__ = BZRC(host, int(port))
		
		realobs = __bzrc__.get_obstacles()
		enemies = __bzrc__.get_othertanks()
		bases = __bzrc__.get_bases()
		flags = __bzrc__.get_flags()
		
		
		plotter = Plot()
		
		plotter.plotToFile(realobs)
		
		plotter.appendToFile(flags, enemies)
		
		#s = raw_input(tanks)
		
		#plotter.plotToFile(plotter.draw_points(flags, "flags"))
		
		plotter.animate(realobs)



    
if __name__ == '__main__':
    main()


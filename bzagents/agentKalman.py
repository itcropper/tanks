#!/usr/bin/python -tt

import sys
import math
import time
import random

from bzrc import BZRC, Command

import OpenGL
OpenGL.ERROR_CHECKING = False
import numpy as np
from numpy import linalg as LA
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

grid = None

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
        self.commands = []

        init_window(int(self.constants["worldsize"]), int(self.constants["worldsize"]))
        
        self.mu=np.matrix([[0],
                           [0],
                           [0],
                           [0],
                           [0],
                           [0]])

        self.Xt = np.matrix([[0],
                             [0],
                             [0],
                             [0],
                             [0],
                             [0]])

        self.F = lambda delta, c :np.matrix([[1, delta/2, delta**2/2,     0,        0,          0],
                                             [0,       1,      delta,     0,        0,          0],
                                             [0,      -c,          1,     0,        0,          0],
                                             [0,       0,          0,     1,    delta, delta**2/2],
                                             [0,       0,          0,     0,        1,      delta],
                                             [0,       0,          0,     0,       -c,          1]])

        pCert = .1
        vCert = 5
        aCert = 40

        self.epsilon  =  np.matrix([[pCert,0,  0,   0,   0,   0],
                                    [0,vCert,  0,   0,   0,   0],
                                    [0,  0,aCert,   0,   0,   0],
                                    [0,  0,  0, pCert,   0,   0],
                                    [0,  0,  0,   0, vCert,   0],
                                    [0,  0,  0,   0,   0, aCert]])

        self.eps0    =   np.matrix([[pCert,0,  0,   0,   0,   0],
                                    [0,vCert,  0,   0,   0,   0],
                                    [0,  0,aCert,   0,   0,   0],
                                    [0,  0,  0, pCert,   0,   0],
                                    [0,  0,  0,   0, vCert,   0],
                                    [0,  0,  0,   0,   0, aCert]])


        self.H = np.matrix([[1, 0, 0, 0, 0, 0],
                            [0, 0, 0, 1, 0, 0]])

        self.Zt = np.matrix([[0, 0]])




        for x in range(len(grid)):
            for y in range(len(grid[x])):
                grid[x][y] = 0.5

    def setEpZ(self, variance):
        self.epZ = np.matrix([[variance**2, 0],
                              [0, variance**2]])

    def update_X(self):
        self.Xt = self.Xt / LA.norm(self.F * self.Xt, self.epsilon)

    def tick(self, time_diff):
        """Some time has passed; decide what to do next."""
        # self.uniform_search(self.bzrc.get_mytanks()[0])
        # return
        mytanks = self.bzrc.get_mytanks()
        self.commands = []

        draw_grid()
        results = self.bzrc.do_commands(self.commands)

    def normalize_angle(self, angle):
        """Make any angle be between +/- pi."""
        angle -= 2 * math.pi * int (angle / (2 * math.pi))
        if angle <= -math.pi:
            angle += 2 * math.pi
        elif angle > math.pi:
            angle -= 2 * math.pi
        return angle


    def updateZt(self):
        self.Zt = self.Zt/LA.norm(self.H * self.Xt, self.epZ)

    def nextK(self, deltaT):
        return (self.F(deltaT, .1)*self.epsilon*np.transpose(self.F(deltaT,.1)) + self.epsilon)*np.transpose(self.H)*LA.inv(self.H * ((self.F(deltaT, .1)*self.epsilon*np.transpose(self.F(deltaT, .1)) + self.epsilon)*np.transpose(self.H)) + self.epZ)


    def nextMu(self, deltaT):
        self.updateZt()
        self.mu = self.F(deltaT, .1) * self.mu + self.nextK(deltaT) * (self.Zt - (self.H * self.mu))
        return self.mu

    def nextEps(self, deltaT):
        return (self.mu.I - self.nextK(deltaT) * self.H )* (self.F(deltaT, .1)*self.epsilon * np.transpose(self.F(deltaT, .1)) + self.epsilon)


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

    #print bzrc.get_constants()

    agent.setEpZ(5)
    
    prev_time = time.time()

    # Run the agent
    try:
        t = True
        while t:
            time_diff = time.time() - prev_time
            agent.tick(time_diff)
            print agent.nextEps(time_diff)

            #print agent.fMatrix(time.time(), prev_time, .1)
            t = False

    except KeyboardInterrupt:
        print "Exiting due to keyboard interrupt."
        bzrc.close()


if __name__ == '__main__':
    main()

# vim: et sw=4 sts=4

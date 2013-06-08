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

        self.mu_timer = 0

        self.bzrc = bzrc
        self.constants = self.bzrc.get_constants()
        self.commands = []

        self.colored = []
        self.targetindex = -1

        init_window(int(self.constants["worldsize"]), int(self.constants["worldsize"]))
        for x in range(len(grid)):
            for y in range(len(grid[x])):
                grid[x][y] = 1

        
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

        self.F = lambda delta    :np.matrix([[1, delta/2, delta**2/2,     0.0,        0.0,          0.0],
                                             [0.0,       1,      delta,     0.0,        0.0,          0.0],
                                             [0.0,     -.1,          1,     0.0,        0.0,          0.0],
                                             [0.0,       0.0,          0.0,     1,    delta, delta**2/2],
                                             [0.0,       0.0,          0.0,     0.0,        1,      delta],
                                             [0.0,       0.0,          0.0,     0.0,      -.1,          1]])

        pCert = 0.1
        vCert = 1.0
        aCert = 80.0

        self.epsilon  =  np.matrix([[pCert,0.0,  0.0,   0.0,   0.0,   0.0],
                                    [0.0,vCert,  0.0,   0.0,   0.0,   0.0],
                                    [0.0,  0.0,aCert,   0.0,   0.0,   0.0],
                                    [0.0,  0.0,  0.0, pCert,   0.0,   0.0],
                                    [0.0,  0.0,  0.0,   0.0, vCert,   0.0],
                                    [0.0,  0.0,  0.0,   0.0,   0.0, aCert]])

        self.eps0    =   np.matrix([[pCert,0.0,  0.0,   0.0,   0.0,   0.0],
                                    [0.0,vCert,  0.0,   0.0,   0.0,   0.0],
                                    [0.0,  0.0,aCert,   0.0,   0.0,   0.0],
                                    [0.0,  0.0,  0.0, pCert,   0.0,   0.0],
                                    [0.0,  0.0,  0.0,   0.0, vCert,   0.0],
                                    [0.0,  0.0,  0.0,   0.0,   0.0, aCert]])

        self.H = np.matrix([[1, 0, 0, 0, 0, 0],
                            [0, 0, 0, 1, 0, 0]])

        self.Zt = np.matrix([[0, 0]])

    def setEpZ(self, variance):
        self.epZ = np.matrix([[variance**2, 0],
                              [0, variance**2]])

    def update_X(self, x, y, delta):
        Xt = np.matrix([[x], 
                        [0], 
                        [0], 
                        [y], 
                        [0], 
                        [0]])

        #Xt = np.transpose(Xt)

        #print Xt, "\n",self.Xt, "\n", self.F(delta)

        mat = self.F(delta) * Xt;

        #print mat
        #print self.epsilon

        self.Xt = self.Xt/(LA.norm(mat, 2) + (LA.norm(self.epsilon)))

    def resetMu(self, x, y):

        self.mu=np.matrix([[x],
                           [0],
                           [0],
                           [y],
                           [0],
                           [0]])
        self.mu_timer = 0

    def tick(self, time_diff):

        """Some time has passed; decide what to do next."""
        tank = self.bzrc.get_mytanks()[0]
        shots = self.bzrc.get_shots()
        self.commands = []
        
        enemytanks = self.bzrc.get_othertanks()
        #Check to see if all enemy tanks are dead and, if they are, return
        if len([t for t in enemytanks if t.status == 'alive']) == 0:
            return

        if self.targetindex == -1:
            self.targetindex = int(random.randint(0, len(enemytanks) -1 ))

        if self.targetindex < 0 or self.targetindex > 2:
            self.targetindex = 0

        #print self.targetindex

        #If our target is dead or uninitialized, find a live tank
        try:
            while enemytanks[self.targetindex].status == 'dead':
                self.targetindex = int(random.randint(0, len(enemytanks)))
        except (IndexError):
            print self.targetindex
            sys.exit(0)


        #reset mu after 200 ticks to compensate for overconfidence
        self.mu_timer += 1
        if self.mu_timer > 2000:
            self.resetMu(enemytanks[self.targetindex].x, enemytanks[self.targetindex].y)
            print "RESET"


        self.updateKalman(enemytanks[self.targetindex], time_diff)

        #print self.mu
        #s = raw_input("")

        #This part iteratively approaches the ideal angle at which to fire at the tank
        dtime = 0
        predictedcoord = ((self.F(0) * self.mu).item(0,0),(self.F(0) * self.mu).item(2,0))
        for i in range(5):
            #For greater precision, increase the range, thereby increasing the number of predictions
            dtime = math.sqrt((predictedcoord[0] - tank.x)**2 + (predictedcoord[1] - tank.y)**2) / float(self.constants["shotspeed"])

            # shootAtMatrix = self.F(dtime) * self.mu
            predictedcoord = ((self.F(dtime) * self.mu).item(0,0),(self.F(dtime) * self.mu).item(2,0))

            # self.draw_x(predictedcoord[0] + int(self.constants["worldsize"]) / 2, predictedcoord[1] + int(self.constants["worldsize"]) / 2, 2, 0)
        
            #print self.mu
            #print shootAtMatrix
            #print predictedcoord
            #s = raw_input(" " )

            #print predictedcoord

        self.shoot(tank, predictedcoord[0], predictedcoord[1])

        #Display stuff
        self.draw_circle(tank.x + int(self.constants["worldsize"]) / 2, tank.y + int(self.constants["worldsize"]) / 2, 10, 0)
        self.draw_circle(self.mu[0][0] + int(self.constants["worldsize"]) / 2, self.mu[3][0] + int(self.constants["worldsize"]) / 2, 5, 0)
        self.draw_x(predictedcoord[0] + int(self.constants["worldsize"]) / 2, predictedcoord[1] + int(self.constants["worldsize"]) / 2, 2, 0)
        for enemy in enemytanks:
            self.draw_x(enemy.x + int(self.constants["worldsize"]) / 2, enemy.y + int(self.constants["worldsize"]) / 2, 10, 0)
        for shot in shots:
            self.draw_x(shot.x + int(self.constants["worldsize"]) / 2, shot.y + int(self.constants["worldsize"]) / 2, 5, 0)
        draw_grid()
        #Clear the display
        while len(self.colored) > 0:
            coord = self.colored.pop()
            grid[coord[0]][coord[1]] = 1

        results = self.bzrc.do_commands(self.commands)

    def shoot(self, tank, x, y):
        ang = math.sqrt((x - tank.x)**2 + (y - tank.y)**2)
        #print tank.x, tank.y, x, y

        angleTol = math.atan2(3, ang)
        self.commands.append(Command(tank.index, 0, 
            1.5 * self.normalize_angle(math.atan2(y - tank.y, x - tank.x) - tank.angle), 
            abs(math.atan2(y - tank.y, x - tank.x) - tank.angle) < angleTol))

    def normalize_angle(self, angle):
        """Make any angle be between +/- pi."""
        angle -= 2 * math.pi * int (angle / (2 * math.pi))
        if angle <= -math.pi:
            angle += 2 * math.pi
        elif angle > math.pi:
            angle -= 2 * math.pi
        return angle

    def draw_circle(self, x, y, radius, color):
        for theta in drange(0, 2 * math.pi, 1.0 / (2 * radius * math.pi)):
            newy = round(x + math.cos(theta) * radius)
            newx = round(y + math.sin(theta) * radius)
            if newx > 0 and newx < len(grid) and newy > 0 and newy < len(grid):
                grid[newx][newy] = color
                if (newx, newy) not in self.colored:
                    self.colored.append((newx, newy))

    def draw_x(self, x, y, radius, color):

        for change in drange(0, radius / math.sqrt(2), 1):
            newy = round(x + change)
            newx = round(y + change)
            if newx > 0 and newx < len(grid) and newy > 0 and newy < len(grid):
                grid[newx][newy] = color
                if (newx, newy) not in self.colored:
                    self.colored.append((newx, newy))
            newy = round(x + change)
            newx = round(y - change)
            if newx > 0 and newx < len(grid) and newy > 0 and newy < len(grid):
                grid[newx][newy] = color
                if (newx, newy) not in self.colored:
                    self.colored.append((newx, newy))
            newy = round(x - change)
            newx = round(y + change)
            if newx > 0 and newx < len(grid) and newy > 0 and newy < len(grid):
                grid[newx][newy] = color
                if (newx, newy) not in self.colored:
                    self.colored.append((newx, newy))
            newy = round(x - change)
            newx = round(y - change)
            if newx > 0 and newx < len(grid) and newy > 0 and newy < len(grid):
                grid[newx][newy] = color
                if (newx, newy) not in self.colored:
                    self.colored.append((newx, newy))
        
    def updateKalman(self, tank, time_diff):
        #self.update_X(tank.x, tank.y, time_diff)
        self.updateZt(tank.x, tank.y)
        #print tank.x, tank.y

        const = self.F(time_diff)*self.epsilon*np.transpose(self.F(time_diff)) + self.eps0

        self.nextMu(time_diff, const)
        self.nextEps(time_diff, const)
        # self.Xt = np.matrix([tank.x],
        #                     [0],
        #                     [0],
        #                     [tank.y],
        #                     [0],
        #                     [0])

    def updateZt(self, x, y):
        '''
        self.update_X(x, y)
        self.Zt = self.ZT / (LA.norm(self.H * self.Xt, 2) + (LA.norm(self.Zt)))
        '''
        self.Zt = np.matrix([[x], [y]])

    def nextK(self, deltaT, const):
        t = ((const)
            *np.transpose(self.H)
            *LA.inv(self.H 
                * const
                *np.transpose(self.H) 
                +self.epZ))

        # print "Inverse: \n", (LA.inv(self.H 
        #         * const
        #         *np.transpose(self.H) 
        #         +self.epZ))

        return t


    def nextMu(self, deltaT, const):
        # print "F, Mu: \n",self.F(deltaT) * self.mu
        # print "Const: \n", const 
        # print "K: \n", self.nextK(deltaT, const)
        # print "Left: \n", (self.Zt - (self.H * self.F(deltaT) * self.mu))
        # print "H: \n", self.H
        # print "Zt: \n", self.Zt

        self.mu = self.F(deltaT) * self.mu + self.nextK(deltaT, const) * (self.Zt - (self.H * self.F(deltaT) * self.mu))
        #print "NEW SELF.MU: \n", self.mu
        #return self.mu

    def nextEps(self, deltaT, const):

        self.epsilon = (np.identity(6) - self.nextK(deltaT, const) * self.H )* (const)

        #print self.mu
        #s = raw_input(" ")

        return self.epsilon


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

    #print bzrc.get_constants()

    agent.setEpZ(5)
    
    prev_time = time.time()

    # Run the agent
    try:
        t = True
        while t:
            time_diff = time.time() - prev_time
            prev_time = time.time()
            agent.tick(time_diff)
            # print agent.nextEps(time_diff)

            #print agent.fMatrix(time.time(), prev_time, .1)
            # t = False

    except KeyboardInterrupt:
        print "Exiting due to keyboard interrupt."
        bzrc.close()


if __name__ == '__main__':
    main()

# vim: et sw=4 sts=4

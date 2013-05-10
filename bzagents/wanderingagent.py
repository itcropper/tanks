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

from bzrc import BZRC, Command

class Agent(object):
    """Class handles all command and control logic for a teams tanks."""

    def __init__(self, bzrc):
        self.bzrc = bzrc
        self.constants = self.bzrc.get_constants()
        self.commands = []
        self.enemycolors = []
        self.bases = self.bzrc.get_bases()
        self.obstacles = self.bzrc.get_obstacles()
        for tank in self.bzrc.get_othertanks():
            if tank.color not in self.enemycolors:
                self.enemycolors.append(tank.color)

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

        for tank in mytanks:
            self.follow_vector(tank)

        results = self.bzrc.do_commands(self.commands)

    def follow_vector(self, tank):
        """Get a vector and follow it!"""
        angle, magnitude = self.get_vector(tank)
        relative_angle = self.normalize_angle(angle - tank.angle)
        command = Command(tank.index, magnitude, relative_angle, True)
        self.commands.append(command)

#    def get_vector(self, tank):
#        best_flag = None
#        best_dist = 2 * float(self.constants['worldsize'])
#        flags = self.bzrc.get_flags()
#        for flag in flags:
#            if flag.color == 'red':
#                continue
#            dist = math.sqrt((flag.x - tank.x)**2 + (flag.y - tank.y)**2)
#            if dist < best_dist:
#                best_dist = dist
#                best_flag = flag
#        if tank.flag == '-' and best_flag != None:
#            return math.atan2(best_flag.y - tank.y, best_flag.x - tank.x), 1
#        #else:
#        #    print 'flag'
#        return math.atan2(-tank.y, -375 - tank.x), 1

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

    def get_vector(self, tank):
        #Here, create a vector by iterating through flags, obstacles and other tanks
        vectors = []
        for obstacle in self.obstacles:
            avgx = 0
            avgy = 0
            for corner in obstacle:
                avgx += corner[0]
                avgy += corner[1]
            avgx /= 4
            avgy /= 4                
            vectors.append(self.repel(tank.x, tank.y, avgx, avgy))
        if tank.flag == '-':
            bestflag = None
            distbest = 2000
            for flag in self.flags:
                if flag.color in self.enemycolors and math.sqrt((flag.x - tank.x)**2 + (flag.y - tank.y)**2) < distbest:
                    distbest = math.sqrt((flag.x - tank.x)**2 + (flag.y - tank.y)**2)
                    bestflag = flag
            if bestflag != None:
                vectors.append(self.attract(tank.x, tank.y, bestflag.x, bestflag.y))
        else:
            for base in self.bases:
                if base.color not in self.enemycolors: 
                    center = ((base.corner1_x + base.corner2_x + base.corner3_x + base.corner4_x)/4,
                              (base.corner1_y + base.corner2_y + base.corner3_y + base.corner4_y)/4)
                    vectors.append(self.attract(tank.x, tank.y, center[0], center[1], 0, 2000))
        
        overallvector = [0, 0]
        for vector in vectors:
            overallvector[0] += vector[0]
            overallvector[1] += vector[1]
        overallvector[0] /= len(vectors)
        overallvector[1] /= len(vectors)
        return math.atan2(overallvector[1], overallvector[0]), math.sqrt(overallvector[0]**2 + overallvector[1]**2) #Angle, Velocity

    def attract(self, targetx, targety, originx, originy, radius = 0, spread = 800):
        theta = math.atan2((originy - targety), (originx - targetx))
        dist = math.sqrt((originy - targety)**2 + (originx - targetx)**2)
        if dist < radius:
            return 0, 0
        elif dist > radius + spread:
            mag = spread * 5
            return mag * math.cos(theta), mag * math.sin(theta)
        else:
            mag = (dist - radius) * 5
            return mag * math.cos(theta), mag * math.sin(theta)

    def baserepel(self, targetx, targety, obstacle, radius, spread):
        pass

    def repel(self, targetx, targety, originx, originy, radius = 25, spread = 100):
        theta = math.atan2(-(originy - targety), -(originx - targetx))
        dist = math.sqrt((originy - targety)**2 + (originx - targetx)**2)
        mag = (spread + radius - dist) * 20
        if dist > radius + spread:
            return 0, 0
        elif dist < radius:
            mag = 1000
        return mag * math.cos(theta), mag * math.sin(theta)

    def tangent(self, targetx, targety, originx, originy, radius = 0, spread = 100):
        theta = self.normalize_angle(math.atan2((originy - targety), (originx - targetx)) + math.pi / 2)
        dist = math.sqrt((originy - targety)**2 + (originx - targetx)**2)
        if dist > radius + spread:
            return 0, 0
        else:
            return (radius + spread - dist) * math.cos(theta), (radius + spread - dist) * math.sin(theta)


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

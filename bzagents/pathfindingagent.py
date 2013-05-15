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
        self.obstacles = self.bzrc.get_obstacles()
        self.othertanks = self.bzrc.get_othertanks()
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

    occgrid = bzrc.get_occgrid(0)
    print len(occgrid)
    print occgrid[0]
    trueocc = []
    for y in occgrid[1]:
        row = []
        for x in occgrid[1][y]:
            row.append(x)
        trueocc.append(y)

    agent.init_screen()
    agent.refresh_screen()
    
    

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

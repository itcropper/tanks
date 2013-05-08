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
import random

from bzrc import BZRC, Command

class Agent(object):
    """Class handles all command and control logic for a teams tanks."""

    def __init__(self, bzrc):
        self.bzrc = bzrc
        self.constants = self.bzrc.get_constants()
        self.commands = []
        mytanks, othertanks, flags, shots = self.bzrc.get_lots_o_stuff()
        self.tankinfo = [{'IsMoving': False, 'TimeMoving': 0, 'Fired': 0, 'CurAngle': tank.angle} for tank in mytanks]

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
            self.dumb_movement(tank, time_diff)

        results = self.bzrc.do_commands(self.commands)

    def dumb_movement(self, tank, time_diff):
        """Duh! Move for 3-8 seconds, then rotate 60 degrees. Shoot every 2 seconds or so!"""
        #if tank.index == 0:
        #    print int(self.tankinfo[tank.index]['TimeMoving']), tank.angle, self.tankinfo[tank.index]['CurAngle']
        self.tankinfo[tank.index]['Fired'] -= time_diff
        self.tankinfo[tank.index]['TimeMoving'] -= time_diff

        isFiring = False
        if self.tankinfo[tank.index]['Fired'] < 0:
            self.tankinfo[tank.index]['Fired'] = random.random() * 2 + 1
            isFiring = True

        if self.tankinfo[tank.index]['IsMoving'] and self.tankinfo[tank.index]['TimeMoving'] < 0:
            self.tankinfo[tank.index]['IsMoving'] = False
            if random.random() > 0.5:
                self.tankinfo[tank.index]['CurAngle'] = self.normalize_angle(self.tankinfo[tank.index]['CurAngle'] + math.pi / 3)
            else:
                self.tankinfo[tank.index]['CurAngle'] = self.normalize_angle(self.tankinfo[tank.index]['CurAngle'] - math.pi / 3)

        if round(tank.angle, 1) == round(self.tankinfo[tank.index]['CurAngle'], 1) and self.tankinfo[tank.index]['TimeMoving'] < 0:
            self.tankinfo[tank.index]['TimeMoving'] = random.random() * 5 + 3
            self.tankinfo[tank.index]['IsMoving'] = True

        speed = 0
        if self.tankinfo[tank.index]['TimeMoving'] > 0:
            speed = 1
        relative_angle = self.normalize_angle(self.tankinfo[tank.index]['CurAngle'] - tank.angle)
        command = Command(tank.index, speed, 2 * relative_angle, isFiring)
        self.commands.append(command)

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
            prev_time = time.time()
            agent.tick(time_diff)
    except KeyboardInterrupt:
        print "Exiting due to keyboard interrupt."
        bzrc.close()


if __name__ == '__main__':
    main()

# vim: et sw=4 sts=4

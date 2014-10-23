#!/usr/bin/python

############################################################
# Generates a client lock/unlock file with commands
############################################################

import os
import sys
import random

def make_lock_file(num_locks, filename):

    cmd_list = []

    lock_set = []

    f = open(filename, "w+")

    # write the lock commands
    while (len(cmd_list) < num_locks):
        lock_num = random.randint(0, 256)
        
        if (not lock_num in lock_set):
            lock_set.append(lock_num)
            cmd_list.append("lock " + str(lock_num))

    # release all the locks
    for lock in lock_set:
        cmd_list.append("unlock " + str(lock))

    for cmd in cmd_list:
        f.write(cmd + "\n")

    f.close()

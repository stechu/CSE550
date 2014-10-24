#!/usr/bin/python

############################################################
# Generates a client lock/unlock file with commands
############################################################

import os
import sys
import random

# Generate a random lock set sequence
def make_lock_file(num_locks, filename):
    cmd_list = []
    lock_set = []

    a_locks = 0
    # generate the lock commands
    while (a_locks < num_locks):
        
        # with probability 50% we unlock a lock
        if (random.randint(0, 100) < 50):
            if (len(lock_set) == 0):
                pass
            else:
                index = random.randint(0, len(lock_set) - 1)
                released_lock = lock_set[index]
                del lock_set[index]
                
                cmd_list.append("unlock " + str(released_lock))
        # otherwise release a lock
        else:
            new_lock = random.randint(0, 256)
            cmd_list.append("lock " + str(new_lock))
            a_locks += 1
            lock_set.append(new_lock)

    # release any remaining locks
    for i in range(0, len(lock_set)):
        released_lock = lock_set[i]
        cmd_list.append("unlock " + str(released_lock))

    f = open(filename, "w+")

    for cmd in cmd_list:
        f.write(cmd + "\n")

    f.close()

def make_simple_file(num_locks, filename):
    cmd_list = []
    lock_set = []

    a_locks = 0

    for i in range(0, num_locks):
        new_lock = random.randint(0, 10)
        cmd_list.append("lock " + str(new_lock))
        cmd_list.append("unlock " + str(new_lock))

    f = open(filename, "w+")

    for cmd in cmd_list:
        f.write(cmd + "\n")

    f.close()

# Generate a contentious lock file sequence which acquires and released the same lock over and over again
def make_contentious_lock_file(num_locks, filename):
    cmd_list = []
    lock_set = []

    # generate the lock commands
    for i in range(0, num_locks):
        cmd_list.append("lock 1337")
        cmd_list.append("unlock 1337")

    # write to file
    f = open(filename, "w+")
    for cmd in cmd_list:
        f.write(cmd + "\n")
    f.close()

# Generate a random lock acquire sequence which has high probability of deadlocking with other files generated by this function
def make_deadlock_file(num_locks, filename):
    cmd_list = []
    lock_set = []

    # generate the lock set
    locks = range(0, 256)

    while (len(lock_set) < num_locks):
        index = random.randint(0, len(locks))
        lock = locks[index]

        cmd_list.append("lock " + str(lock))
        del locks[index]

    assert(len(lock_set) == 256)
    assert(len(cmd_list) == 256)

    for i in range(0, 256):
        cmd_list.append("unlock " + str(i))

    # write file 
    f = open(filename, "w+")
    for cmd in cmd_list:
        f.write(cmd + "\n")
    f.close()

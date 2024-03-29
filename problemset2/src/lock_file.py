#!/usr/bin/python

############################################################
# Generates a client lock/unlock file with commands
############################################################

import os
import random


def make_lock_file(num_locks, filename):
    """
        Generate a random lock set sequence
    """
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
    """
        generate lock and unlock commands
    """
    cmd_list = []

    for i in range(0, num_locks):
        new_lock = i
        cmd_list.append("lock " + str(new_lock))
        cmd_list.append("unlock " + str(new_lock))

    f = open(filename, "w+")

    for cmd in cmd_list:
        f.write(cmd + "\n")

    f.close()


def make_contentious_lock_file(num_locks, filename):
    """
        Generate a contentious lock file sequence which acquires and released
        the same lock over and over again
    """
    cmd_list = []

    # generate the lock commands
    for i in range(0, num_locks):
        cmd_list.append("lock 1337")
        cmd_list.append("unlock 1337")

    # write to file
    f = open(filename, "w+")
    for cmd in cmd_list:
        f.write(cmd + "\n")
    f.close()


def make_deadlock_file(num_locks, filename):
    """
        Generate a random lock acquire sequence which has high probability of
        deadlocking with other files generated by this function
    """
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


def validate_lock_file(filename):
    """
        Validates if the sequence of locks forms a correct locking pattern
    """
    print "Validating lock file: " + filename

    f = open(filename, "r+")

    lock_set = []

    for line in f:
        linet = line.strip(" \t\n")
        fields = linet.split("-")
        assert(len(fields) == 3)

        cmd = fields[2].strip("\n \t")

        cmd_fields = cmd.split(" ")
        assert(len(cmd_fields) == 2)

        cmd_type = cmd_fields[0]
        lock_num = int(cmd_fields[1])

        if (cmd_type == "lock"):
            assert(not lock_num in lock_set)
            lock_set.append(lock_num)
            assert(lock_num in lock_set)
        elif (cmd_type == "unlock"):
            assert(lock_num in lock_set)
            lock_set.remove(lock_num)
            assert(not lock_num in lock_set)
        else:
            return False

    print "OK!"

    return True


# Validate if the client file made it into the server logs
def validate_client_file(client_files, server_files):

    assert(len(client_files) > 0)
    assert(len(server_files) > 0)

    print "Validated all client requests appear in a server log..."

    # find the most complete server log
    server_log = None
    longest_log = -1
    for s in server_files:
        log_dump = os.popen("wc -l " + s).read()
        log_fields = log_dump.lstrip(" ").split(" ")
        log_size = log_fields[0]
        log_length = int(log_size)
        if (log_length > longest_log):
            server_log = s
            longest_log = log_length

    # load the longest server file and build its command distribution
    server_dist = dict()
    cmd_list = dict()

    f = open(server_log, "r+")
    for line in f:
        linet = line.strip(" \t\n")
        fields = linet.split("-")
        assert(len(fields) == 3)

        cmd = fields[2].strip("\n \t")

        cmd_fields = cmd.split(" ")
        assert(len(cmd_fields) == 2)

        cmd_type = cmd_fields[0]
        lock_num = int(cmd_fields[1])

        entry = cmd_type + " " + str(lock_num)
        assert(int(fields[0]) not in cmd_list)
        cmd_list[int(fields[0])] = entry

        if entry in server_dist:
            server_dist[entry] += 1
        else:
            server_dist[entry] = 1
    f.close()

    cli_dist = dict()

    # load the client files and aggregate it's command distributions
    for cfile in client_files:
        cf = open(cfile, "r+")
        for line in cf:
            linet = line.strip(" \t\n")

            if (linet in cli_dist):
                cli_dist[linet] += 1
            else:
                cli_dist[linet] = 1

    cf.close()

    # compare the command distributions and make sure they're the same
    for key in cli_dist:
        assert key in server_dist
        assert cli_dist[key] == server_dist[key]

    print "OK!"

    print "Validating state machine is correctly replicated..."

    # validate that each of the shorter server logs matches the
    # instance resolutions of the main server log
    for f in server_files:

        # don't validte the longest server log against itself
        if (f == server_log):
            continue

        check_file = open(f, "r+")
        for line in check_file:
            linet = line.strip(" \t\n")
            fields = linet.split("-")
            assert(len(fields) == 3)

            cmd = fields[2].strip("\n \t")

            cmd_fields = cmd.split(" ")
            assert(len(cmd_fields) == 2)

            cmd_type = cmd_fields[0]
            lock_num = int(cmd_fields[1])

            instance = int(fields[0])
            cmd = cmd_type + " " + str(lock_num)

            # check that the command for that instance matches
            # against the master
            assert(cmd_list[instance] == cmd)

    print "OK!"

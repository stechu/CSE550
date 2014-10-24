#!/usr/bin/python

#########################################################################
# failure_test.py
#########################################################################

import server
import sys
import os
import unittest
import command
import pickle
import socket
import subprocess
import time
import message
from multiprocessing import Queue, Process, Lock
import random
from lock_file import *
import client

class msg_failure_test(unittest.TestCase):

    ###############################################################
    # Bring up a full Paxos group with multiple server instances
    ###############################################################

    def setUp(self):
        pass

    ###############################################################
    # Test Functionality at 50% Message Drop Rate
    ###############################################################

    def test_message_drops(self):

        # set test server size
        self.TOTAL_SERVERS = 5

        # initialize server list
        self.server_list = []

        # generate the host numbers and ports of server connections
        for i in range(9000, 9000 + 2 * self.TOTAL_SERVERS, 2):
            server_entry = dict()

            server_entry["host"] = "localhost"
            server_entry["internal_port"] = i + 1
            server_entry["client_port"] = i
            server_entry["drop_rate"] = 50 # this is a percentage

            self.server_list.append(server_entry)

        print self.server_list

        # bring up each server
        self.servers = []

        # iterate through address list and instantiate servers
        for i in range(0, len(self.server_list)):
            # instantiate new servers
            new_server = server.PAXOS_member(i, self.server_list)
            self.servers.append(new_server)

        assert(len(self.servers) == len(self.server_list))
        assert(len(self.servers) == self.TOTAL_SERVERS)

        # initialize new servers
        for i in range(0, len(self.servers)):
            s = self.server_list[i]
            assert s
            self.servers[i].initialize_paxos()
            time.sleep(.5) # allow the system to recover

        LOCKS = 100

        # generate the lock files
        for i in range(0, len(self.server_list)):
            filename = "client_" + str(i) + ".txt"
            make_simple_file(LOCKS, filename)

        # instantiate a client to each server
        client_list = []
        for i in range(0, len(self.server_list)):
            port = self.server_list[i]["client_port"]
            host = self.server_list[i]["host"]
            assert((int(port) % 2) == 0)

            cli = client.client(
                "client_" + str(i) + ".txt", host, port, len(client_list))
            client_list.append(cli)

        # join each client
        failed = False
        for c in client_list:
            try:
                c.c_process.join()
            except Exception, e:
                c.terminate()
                failed = True

        assert(not failed)

    ###############################################################
    # Test Functionality at 50% Message Duplication Rate
    ###############################################################

    def test_message_duplication(self):

        # set test server size
        self.TOTAL_SERVERS = 5

        # initialize server list
        self.server_list = []

        # generate the host numbers and ports of server connections
        for i in range(9000, 9000 + 2 * self.TOTAL_SERVERS, 2):
            server_entry = dict()

            server_entry["host"] = "localhost"
            server_entry["internal_port"] = i + 1
            server_entry["client_port"] = i
            server_entry["dup_rate"] = 50 # this is a percentage

            self.server_list.append(server_entry)

        print self.server_list

        # bring up each server
        self.servers = []

        # iterate through address list and instantiate servers
        for i in range(0, len(self.server_list)):
            # instantiate new servers
            new_server = server.PAXOS_member(i, self.server_list)
            self.servers.append(new_server)

        assert(len(self.servers) == len(self.server_list))
        assert(len(self.servers) == self.TOTAL_SERVERS)

        # initialize new servers
        for i in range(0, len(self.servers)):
            s = self.server_list[i]
            assert s
            self.servers[i].initialize_paxos()
            time.sleep(.5) # allow the system to recover

        LOCKS = 100

        # generate the lock files
        for i in range(0, len(self.server_list)):
            filename = "client_" + str(i) + ".txt"
            make_simple_file(LOCKS, filename)

        # instantiate a client to each server
        client_list = []
        for i in range(0, len(self.server_list)):
            port = self.server_list[i]["client_port"]
            host = self.server_list[i]["host"]
            assert((int(port) % 2) == 0)

            cli = client.client(
                "client_" + str(i) + ".txt", host, port, len(client_list))
            client_list.append(cli)

        # join each client
        failed = False
        for c in client_list:
            try:
                c.c_process.join()
            except Exception, e:
                c.terminate()
                failed = True

        assert(not failed)

    ###############################################################
    # Test Functionality at 50% Message Duplication and Drop Rate
    ###############################################################
    def test_message_drops(self):

        # set test server size
        self.TOTAL_SERVERS = 5

        # initialize server list
        self.server_list = []

        # generate the host numbers and ports of server connections
        for i in range(9000, 9000 + 2 * self.TOTAL_SERVERS, 2):
            server_entry = dict()

            server_entry["host"] = "localhost"
            server_entry["internal_port"] = i + 1
            server_entry["client_port"] = i
            server_entry["dup_rate"] = 0.5
            server_entry["drop_rate"] = 0.5

            self.server_list.append(server_entry)

        print self.server_list

        # bring up each server
        self.servers = []

        # iterate through address list and instantiate servers
        for i in range(0, len(self.server_list)):
            # instantiate new servers
            new_server = server.PAXOS_member(i, self.server_list)
            self.servers.append(new_server)

        assert(len(self.servers) == len(self.server_list))
        assert(len(self.servers) == self.TOTAL_SERVERS)

        # initialize new servers
        for i in range(0, len(self.servers)):
            s = self.server_list[i]
            assert s
            self.servers[i].initialize_paxos()
            time.sleep(.5) # allow the system to recover

        LOCKS = 100

        # generate the lock files
        for i in range(0, len(self.server_list)):
            filename = "client_" + str(i) + ".txt"
            make_simple_file(LOCKS, filename)

        # instantiate a client to each server
        client_list = []
        for i in range(0, len(self.server_list)):
            port = self.server_list[i]["client_port"]
            host = self.server_list[i]["host"]
            assert((int(port) % 2) == 0)

            cli = client.client(
                "client_" + str(i) + ".txt", host, port, len(client_list))
            client_list.append(cli)

        # join each client
        failed = False
        for c in client_list:
            try:
                c.c_process.join()
            except Exception, e:
                c.terminate()
                failed = True

        assert(not failed)

    ###############################################################
    # Shutdown the Paxos group
    ###############################################################

    def tearDown(self):

        # directly inject an exit message to each of the queues
        exit_msg = message.message(message.MESSAGE_TYPE.EXIT,
                                   None, None, None, 'localhost', 9000, None)
 
        for s in self.servers:
            s.acceptor_queue.put(exit_msg)
            s.proposer_queue.put(exit_msg)

        # join the acceptor and proposer processes for each server
        for s in self.servers:
            s.listening_process.terminate()
            s.listening_process.join(5)
            s.acceptor_process.join(5)
            s.proposer_process.join(5)

if __name__ == '__main__':
    unittest.main()

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

class failure_test(unittest.TestCase):

    ###############################################################
    # Bring up a full Paxos group with multiple server instances
    ###############################################################

    def setUp(self):

        # set test server size
        self.TOTAL_SERVERS = 3

        # initialize server list
        self.server_list = []

        # generate the host numbers and ports of server connections
        for i in range(9001, 9001 + 2 * self.TOTAL_SERVERS, 2):
            port = i
            host = 'localhost'

            self.server_list.append((host, port))

        # bring up each server
        self.servers = []

        # iterate through address list and instantiate servers
        for addr in self.server_list:
            assert(len(addr) == 2)
            client_port = addr[1] - 1
            host = addr[0]

            # instantiate new servers
            new_server = server.server(host, client_port, len(self.servers), len(self.server_list))

            self.servers.append(new_server)

        assert(len(self.servers) == len(self.server_list))
        assert(len(self.servers) == self.TOTAL_SERVERS)

        # initialize new servers
        for i in range(0, len(self.servers)):
            s = self.server_list[i]
            assert(s != None)
            assert(((s[1]-1) % 2) == 0)
            self.servers[i].initialize_paxos(s[0], s[1] - 1, i, len(self.servers), self.server_list)

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
            s.listening_process.join(1)
            if (s.listening_process.is_alive()):
                s.listening_process.terminate()
                s.listening_process.join(1)

            s.acceptor_process.join(1)
            if (s.acceptor_process.is_alive()):
                s.acceptor_process.terminate()
                s.acceptor_process.join(1)
 
            s.proposer_process.join(1)
            if (s.proposer_process.is_alive()):
                s.proposer_process.terminate(1)
                s.proposer_process.join(1)

    ##########################################################
    # Test if Paxos group completes even with single node
    #  experiencing a failure
    # Do not attempt recovery
    ##########################################################

    def test_single_server_failure(self):

        # randomly compute a server index to kill
        server_index = random.randint(0, len(server_list))
        assert(server_index < len(server_list))
        s = self.servers[server_index]

        # write a bunch of lock files
        client_list = []
        for i in range(0, len(self.server_list)):
            lock_file(100, "client_" + str(i) + ".txt")

        # start a bunch of clients
        for i in range(0, len(self.server_list)):
            (host, port) = self.server_list[i]
            port = port - 1
            assert((port % 2) == 0)
            new_client = client.client("client_" + str(i) + ".txt", host, port, i)

        # kill the randomly selected server's processes
        s.proposer_process.terminate()
        s.acceptor_process.terminate()
        s.listening_process.terminate()

    def test_multi_server_failure(self):
        
        # write a bunch of lock files
        client_list = []
        for i in range(0, len(self.server_list)):
            lock_file(100, "client_" + str(i) + ".txt")

        # start a bunch of clients
        for i in range(0, len(self.server_list)):
            (host, port) = self.server_list[i]
            port = port - 1
            assert((port % 2) == 0)
            new_client = client.client("client_" + str(i) + ".txt", host, port, i)

        # randomly kill the first set of servers until you've killed slightly less than a majority
        for i in range(0, int(len(self.servers)/2)):
            s = self.servers[i]
            s.listening_process.terminate()
            s.proposer_process.terminate()
            s.acceptor_process.terminate()
        


if __name__ == '__main_':
    unittest.main()
